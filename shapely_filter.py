from shapely.geometry import MultiLineString
from shapely.ops import unary_union, linemerge
import itertools


class LineFilter:
    """A simple attempt to simplify or filter a MultiLineString."""

    def __init__(self, multi_line):
        """Initialize attributes to the filter."""
        self.multi_line = multi_line
        self.length = 1000

    def update_length(self, length):
        """Set the length to the given value.
        Parameter:
            length (int) - lines shorter than this length will be removed,
                default is 1000 (e.g., in meter)."""
        self.length = length

    def remove_dead_end(self, is_simplest=True, level=None):
        """Remove short dead-end lines. Dead end lines intersect only one other
        line.
        Parameter:
            is_simplest (bool) - if True, network will return its simplest form.
                if False, level of simplification should be given.
            level (int) - level of simplification (how many times the network
                will be simplified). if None, is_simplest should be True.
        Returns: a filtered network (a MultiLineString)."""
        filtered = self.multi_line
        while is_simplest:
            # pack the end point (start and end) coordinates of each line
            ends = []
            for line_index in range(len(filtered)):
                start, *_, end = filtered[line_index].coords
                ends.append(start)
                ends.append(end)

            # pack dead-end lines with length shorter than the given length
            short_dead_ends = []
            for line_index in range(len(filtered)):
                if ends.count(filtered[line_index].coords[0]) == 1 \
                        and ends.count(filtered[line_index].coords[-1]) > 1:
                    if filtered[line_index].length < self.length:
                        short_dead_ends.append(filtered[line_index])
                elif ends.count(filtered[line_index].coords[0]) > 1 \
                        and ends.count(filtered[line_index].coords[-1]) == 1:
                    if filtered[line_index].length < self.length:
                        short_dead_ends.append(filtered[line_index])

            # filter out short lines
            filtered = [line for line in filtered
                        if line not in short_dead_ends]
            filtered = unary_union(filtered)
            filtered = linemerge(filtered)
            # if short_dead_ends is empty
            if not short_dead_ends:
                break
            filtered = MultiLineString(filtered)
        else:
            for level_index in range(level):
                ends = []
                for line_index in range(len(filtered)):
                    start, *_, end = filtered[line_index].coords
                    ends.append(start)
                    ends.append(end)

                short_dead_ends = []
                for line_index in range(len(filtered)):
                    if ends.count(filtered[line_index].coords[0]) == 1 \
                            and ends.count(filtered[line_index].coords[-1]) > 1:
                        if filtered[line_index].length < self.length:
                            short_dead_ends.append(filtered[line_index])
                    elif ends.count(filtered[line_index].coords[0]) > 1 \
                            and ends.count(filtered[line_index].coords[-1]) \
                            == 1:
                        if filtered[line_index].length < self.length:
                            short_dead_ends.append(filtered[line_index])

                filtered = [line for line in filtered
                            if line not in short_dead_ends]
                filtered = unary_union(filtered)
                filtered = linemerge(filtered)
        return filtered

    def remove_disjoint(self):
        """Remove short disjoint lines that their boundary and interior do not
        intersect at all with those of the other.
        Returns: a filtered network (a MultiLineString)."""
        # pack lines that intersecting each other
        # consider the order
        result = itertools.permutations(self.multi_line, 2)
        intersected = [line1 for (line1, line2) in result
                       if line1.intersects(line2)]

        # pack disjoint lines with length shorter than the given length
        short_disjoint = [line for line in self.multi_line if
                          line not in intersected
                          and line.length < self.length]

        # filter out short disjoint lines
        filtered = [line for line in self.multi_line
                    if line not in short_disjoint]
        filtered = MultiLineString(filtered)
        return filtered

    def remove_ring(self):
        """Remove self-contained rings that share the same endpoint. Note that
        disjoint rings are also disjoint lines, thus will be removed already
        when using remove_disjoint() method, if their length are shorter than
        the given length.
        Returns: a filtered network (a MultiLineString)."""
        rings = []
        for line_index in range(len(self.multi_line)):
            if self.multi_line[line_index].coords[0] \
                    == self.multi_line[line_index].coords[-1]:
                rings.append(self.multi_line[line_index])

        # filter out rings
        filtered = [line for line in self.multi_line
                    if line not in rings]
        filtered = MultiLineString(filtered)
        return filtered

    def remove_oxbow(self):
        """Remove U-shaped bend (oxbow lakes) from a river or stream, which is
        cut off from the main stream and still connected to the main stream at
        its both ends. All lines that share the same ends (start- and end point)
        will be compared with each other once, then return the shortest line.
        Returns: a filtered network (a MultiLineString)."""
        # pack all oxbow lakes, which are all longer than the cut off channel
        oxbow = []
        for i in range(len(self.multi_line)):
            for j in range(i + 1, len(self.multi_line)):
                start_i, *_, end_i = self.multi_line[i].coords
                start_j, *_, end_j = self.multi_line[j].coords
                ends_i = (start_i, end_i)
                ends_j = (start_j, end_j)
                ends_j_reverse = (end_j, start_j)  # consider line direction
                if ends_i == ends_j or ends_i == ends_j_reverse:
                    # check if they share the same ends
                    # if so, append the oxbow one to the new list
                    if self.multi_line[i].length > self.multi_line[j].length:
                        oxbow.append(self.multi_line[i])
                    else:
                        oxbow.append(self.multi_line[j])

        # filter out all oxbow lakes
        filtered = [line for line in self.multi_line if line not in oxbow]
        filtered = MultiLineString(filtered)
        return filtered

    def simplify_line(self, is_simplest=True, level=None,
                      remove_ring=True, remove_oxbow=True):
        """Simplify line geometry by removing short dead-end, short disjoint
         lines, disjoint rings, and oxbow lakes.
        Parameters:
            is_simplest (bool) - if True, network will return its simplest form.
                if False, level of simplification should be given.
            level (int) - level of simplification (how many times the network
                will be simplified). if None, is_simplest should be True.
            remove_ring (bool) - if True, remove disjoint self-contained rings
                that share the same endpoints.
            remove_oxbow (bool) - if True, remove U-shaped bends (oxbow lakes)
                from river meanders, return the shortest channel.
        Returns: a filtered network (a MultiLineString)."""
        # Remove short dead-end lines
        filtered = self.multi_line
        while is_simplest:
            # pack the end point (start and end) coordinates of each line
            ends = []
            for line_index in range(len(filtered)):
                start, *_, end = filtered[line_index].coords
                ends.append(start)
                ends.append(end)

            # pack dead-end lines with length shorter than the given length
            short_dead_ends = []
            for line_index in range(len(filtered)):
                if ends.count(filtered[line_index].coords[0]) == 1 \
                        and ends.count(filtered[line_index].coords[-1]) > 1:
                    if filtered[line_index].length < self.length:
                        short_dead_ends.append(filtered[line_index])
                elif ends.count(filtered[line_index].coords[0]) > 1 \
                        and ends.count(filtered[line_index].coords[-1]) == 1:
                    if filtered[line_index].length < self.length:
                        short_dead_ends.append(filtered[line_index])

            # filter out short dead-end lines
            filtered = [line for line in filtered
                        if line not in short_dead_ends]
            filtered = unary_union(filtered)
            filtered = linemerge(filtered)

            if not short_dead_ends:
                break

        else:
            # Remove dead-end lines
            for level_index in range(level):
                ends = []
                for line_index in range(len(filtered)):
                    start, *_, end = filtered[line_index].coords
                    ends.append(start)
                    ends.append(end)

                short_dead_ends = []
                for line_index in range(len(filtered)):
                    if ends.count(filtered[line_index].coords[0]) == 1 \
                            and ends.count(filtered[line_index].coords[-1]) > 1:
                        if filtered[line_index].length < self.length:
                            short_dead_ends.append(filtered[line_index])
                    elif ends.count(filtered[line_index].coords[0]) > 1 \
                            and ends.count(filtered[line_index].coords[-1]) \
                            == 1:
                        if filtered[line_index].length < self.length:
                            short_dead_ends.append(filtered[line_index])

                filtered = [line for line in filtered
                            if line not in short_dead_ends]
                filtered = unary_union(filtered)
                filtered = linemerge(filtered)

        # Remove short disjoint lines
        result = itertools.permutations(filtered, 2)
        intersected = [line1 for (line1, line2) in result
                       if line1.intersects(line2)]

        short_disjoint = [line for line in filtered if
                          line not in intersected
                          and line.length < self.length]

        # Remove ring
        if remove_ring:
            rings = []
            for line_index in range(len(filtered)):
                if filtered[line_index].coords[0] \
                        == filtered[line_index].coords[-1]:
                    rings.append(filtered[line_index])

            # Remove oxbow lakes
            if remove_oxbow:
                oxbow = []
                for i in range(len(filtered)):
                    for j in range(i + 1, len(filtered)):
                        start_i, *_, end_i = filtered[i].coords
                        start_j, *_, end_j = filtered[j].coords
                        ends_i = (start_i, end_i)
                        ends_j = (start_j, end_j)
                        ends_j_reverse = (
                            end_j, start_j)  # consider line direction
                        if ends_i == ends_j or ends_i == ends_j_reverse:
                            # check if they share the same ends
                            # if so, append the longer one to the new list
                            if filtered[i].length > filtered[j].length:
                                oxbow.append(filtered[i])
                            else:
                                oxbow.append(filtered[j])

                filtered = [line for line in filtered
                            if line not in short_disjoint
                            and line not in rings
                            and line not in oxbow]
                filtered = MultiLineString(filtered)
            else:
                filtered = [line for line in filtered
                            if line not in short_disjoint
                            and line not in rings]
                filtered = MultiLineString(filtered)
        else:
            # Remove oxbow lakes
            if remove_oxbow:
                oxbow = []
                for i in range(len(filtered)):
                    for j in range(i + 1, len(filtered)):
                        start_i, *_, end_i = filtered[i].coords
                        start_j, *_, end_j = filtered[j].coords
                        ends_i = (start_i, end_i)
                        ends_j = (start_j, end_j)
                        ends_j_reverse = (
                            end_j, start_j)  # consider line direction
                        if ends_i == ends_j or ends_i == ends_j_reverse:
                            # check if they share the same ends
                            # if so, append the longer one to the new list
                            if filtered[i].length > filtered[j].length:
                                oxbow.append(filtered[i])
                            else:
                                oxbow.append(filtered[j])

                filtered = [line for line in filtered
                            if line not in short_disjoint
                            and line not in oxbow]
                filtered = MultiLineString(filtered)
            else:
                filtered = [line for line in filtered
                            if line not in short_disjoint]
                filtered = MultiLineString(filtered)
        return filtered
