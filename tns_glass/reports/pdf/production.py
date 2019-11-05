from decimal import Decimal, ROUND_HALF_UP

class ProductionRow(object):

    def __init__(self, grade, volume, subrows=None):
        self.name = grade.name
        self.grade = grade
        self.volume = volume

        if not subrows:
            self.rows = []
        else:
            self.rows = subrows
            
            # populate our percentages
            for row in self.rows:
                percent = Decimal("0")
                if row.volume > Decimal("0"):
                    percent = (row.volume * Decimal("100") / self.volume).quantize(1, rounding=ROUND_HALF_UP)

                row.percent = percent

class ProductionBox(object):

    def __init__(self, report):
        self.report = report
        self.categories = self.build_category_rows()
        self.build_ratios()

        # figure out our utilization
        if self.report.capacity:
            self.utilization = (self.parchment_total / self.report.capacity * Decimal('100')).quantize(1, rounding=ROUND_HALF_UP)
        else:
            self.utilization = None

        # figure out our production of the top grade (or just green)
        self.calculate_top_grade_stats()

    def calculate_top_grade_stats(self):
        # first, do we have a top grade?
        self.has_top_grade = False
        for grade in self.report.season.get_grade_tree():
            if grade.is_top_grade:
                self.has_top_grade = True
                break

        # if we don't, then our total is just our total green
        if not self.has_top_grade:
            self.top_grade_total = self.green_total

        # otherwise, sum up all our production values that are our top grade
        else:
            total = Decimal("0")
            for category in self.categories:
                if category.rows:
                    for row in category.rows:
                        if row.grade.kind == 'GRE' and row.grade.is_top_grade:
                            total += row.volume

            self.top_grade_total = total
            
        # ratio of top grade to cherry
        self.cherry_to_top_grade_ratio = self.calculate_ratio(self.cherry_total, self.top_grade_total)

        # now figure out the ratio of the top grade to all green
        if self.green_total and self.has_top_grade:
            self.top_grade_percentage = (self.top_grade_total / self.green_total * Decimal('100')).quantize(1, rounding=ROUND_HALF_UP)
        else:
            self.top_grade_percentage = None

    def get_categories(self):
        return self.categories
    
    def get_grade_volume(self, grade):
        output = self.report.production.filter(grade=grade)
        if output:
            return output[0].volume
        else:
            return Decimal("0")

    def calculate_ratio(self, numerator, denominator):
        if denominator > Decimal("0"):
            return numerator / denominator
        else:
            return Decimal("0")

    def build_ratios(self):
        # these totals are for the volume that is processed, ie, goes on to the next stage
        # they do not include totals that are not washed
        self.cherry_total = self.volume_for_kind('CHE', True)
        self.parchment_total = self.volume_for_kind('PAR', True)
        self.green_total = self.volume_for_kind('GRE', True)

        # these ratios take into account the washed / unwashed distinction above

        # ratio of washed cherry to ALL parchment
        self.cherry_to_parchment_ratio = self.calculate_ratio(self.cherry_total, self.volume_for_kind('PAR'))

        # ratio of washed cherry to green that is also washed
        self.parchment_to_green_ratio = self.calculate_ratio(self.parchment_total, self.green_total)

        # ratio of washed cherry that makes it to be washed green
        self.cherry_to_green_ratio = self.cherry_to_parchment_ratio * self.parchment_to_green_ratio

    def volume_for_kind(self, kind, only_processed=False):
        total = Decimal("0")
        for category in self.categories:
            if category.rows:
                for row in category.rows:
                    if row.grade.kind == kind and (not only_processed or not row.grade.is_not_processed):
                        total += row.volume
            else:
                if category.grade.kind == kind and (not only_processed or not category.grade.is_not_processed):
                    total += category.volume

        return total

    def build_subrow(self, tree, index):
        sub_grade = tree[index]
        sub_volume = self.get_grade_volume(sub_grade)

        for i in range(index+1, len(tree)):
            grade = tree[i]

            if grade.depth <= 1:
                break

            sub_volume += self.get_grade_volume(grade)

        return ProductionRow(sub_grade, sub_volume)

    def build_production_row(self, tree, index):
        parent_grade = tree[index]
        parent_volume = self.get_grade_volume(parent_grade)
        subrows = []

        for i in range(index+1, len(tree)):
            grade = tree[i]

            # new parent grade, break out, we are done
            if grade.depth == 0:
                break

            # new subrow
            if grade.depth == 1:
                subrow = self.build_subrow(tree, i)
                parent_volume += subrow.volume
                subrows.append(subrow)

        return ProductionRow(parent_grade, parent_volume, subrows)

    def build_category_rows(self):
        rows = []

        # get our tree of grades for this season
        grade_tree = self.report.season.get_grade_tree()

        # for each top level grade, build a row
        for (index, grade) in enumerate(grade_tree):
            if grade.depth == 0:
                rows.append(self.build_production_row(grade_tree, index))

        return rows
