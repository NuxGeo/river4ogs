from shapely.geometry import MultiLineString


class LineFilter():
    """A simple attempt to simplify or filter a MultiLineString."""

    def __init__(self, mline):
        """Initialize mline attribute."""
        self.mline = mline

    def remove_disconnected(self, length=4000):
        """Remove disconnected lines based on their length.
        default: lines shorter than 4000m will be removed."""
        # select lines that intersecting each other
        intersection = []
        for i in range(len(self.mline)):
            for j in range(i + 1, len(self.mline)):
                if self.mline[i].intersects(self.mline[j]):
                    intersection.append(self.mline[i])
                    intersection.append(self.mline[j])

        # remove duplicates
        uniq_intersection = []
        for line in intersection:
            if not any(p.equals(line) for p in uniq_intersection):
                uniq_intersection.append(line)

        uniq_intersection = MultiLineString(uniq_intersection)

        isolated = [line for line in self.mline if
                    line not in uniq_intersection]

        # filter out lines that are shorter than the given length
        isolated_short = [line for line in isolated if line.length < length]
        filtered = [line for line in self.mline if line not in isolated_short]
        filtered = MultiLineString(filtered)
        return filtered

    def remove_oxbow(self):
        """Remove U-shaped bend in a line (e.g., river or stream), which is cut
        off from the main stream. All lines that share the same ends (start- and
        end point) will be compared with each other once, then the shortest line
        will be returned."""
        # select all oxbow bends, non of which is the shortest
        longer = []
        for i in range(len(self.mline)):
            for j in range(i + 1, len(self.mline)):
                start_i, *_, end_i = self.mline[i].coords
                start_j, *_, end_j = self.mline[j].coords
                ends_i = (start_i, end_i)
                ends_j = (start_j, end_j)
                ends_j_reverse = (end_j, start_j)  # consider line direction
                if ends_i == ends_j or ends_i == ends_j_reverse:
                    # check if they share the same ends
                    # if so, append the longer one to the new list
                    if self.mline[i].length > self.mline[j].length:
                        longer.append(self.mline[i])
                    else:
                        longer.append(self.mline[j])

        # remove duplicates
        uniq_longer = []
        for line in longer:
            if not any(p.equals(line) for p in uniq_longer):
                uniq_longer.append(line)

        filtered = [line for line in self.mline if line not in uniq_longer]
        filtered = MultiLineString(filtered)
        return filtered

    def remove_disconnected_and_oxbow(self, length=4000):
        """Remove both disconnected lines and oxbows."""
        intersection = []
        for i in range(len(self.mline)):
            for j in range(i + 1, len(self.mline)):
                if self.mline[i].intersects(self.mline[j]):
                    intersection.append(self.mline[i])
                    intersection.append(self.mline[j])

        # remove duplicates
        uniq_intersection = []
        for line in intersection:
            if not any(p.equals(line) for p in uniq_intersection):
                uniq_intersection.append(line)

        uniq_intersection = MultiLineString(uniq_intersection)

        isolated = [line for line in self.mline if
                    line not in uniq_intersection]

        # filter out lines that are shorter than the given length
        isolated_short = [line for line in isolated if line.length < length]

        longer = []
        for i in range(len(self.mline)):
            for j in range(i + 1, len(self.mline)):
                start_i, *_, end_i = self.mline[i].coords
                start_j, *_, end_j = self.mline[j].coords
                ends_i = (start_i, end_i)
                ends_j = (start_j, end_j)
                ends_j_reverse = (end_j, start_j)  # consider line direction
                if ends_i == ends_j or ends_i == ends_j_reverse:
                    # check if they share the same ends
                    # if so, append the longer one to the new list
                    if self.mline[i].length > self.mline[j].length:
                        longer.append(self.mline[i])
                    else:
                        longer.append(self.mline[j])

        # remove duplicates
        uniq_longer = []
        for line in longer:
            if not any(p.equals(line) for p in uniq_longer):
                uniq_longer.append(line)

        filtered1 = [line for line in self.mline if line not in uniq_longer]
        filtered2 = [line for line in filtered1 if line not in isolated_short]
        filtered2 = MultiLineString(filtered2)
        return filtered2
