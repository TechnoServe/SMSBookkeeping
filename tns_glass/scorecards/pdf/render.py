import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth, getAscent, getDescent

from canvas.page import PDFPage

from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils.translation import activate

class PDFScorecard(PDFPage):
    PERCENT = 10
    BOOL_STRING = 11

    AUDIT_ROW_COLS = ((100, PDFPage.BOX_FONT_BOLD, PDFPage.LEFT), (100, PDFPage.BOX_FONT, PDFPage.LEFT))

    SUMMARY_BOX_HEADER_COLS = ((285, PDFPage.BOX_FONT_BOLD, PDFPage.LEFT), (150, PDFPage.BOX_FONT_BOLD, PDFPage.RIGHT), (150, PDFPage.BOX_FONT_BOLD, PDFPage.RIGHT))
    SUMMARY_BOX_CATEGORY_COLS = ((285, PDFPage.BOX_FONT_BOLD, PDFPage.LEFT), (150, PDFPage.BOX_FONT, PDFPage.RIGHT, BOOL_STRING), (150, PDFPage.BOX_FONT, PDFPage.RIGHT, PERCENT))
    SUMMARY_BOX_ROW_COLS = ((270, PDFPage.BOX_ITALIC, PDFPage.LEFT), (160, PDFPage.BOX_ITALIC, PDFPage.RIGHT, BOOL_STRING), (160, PDFPage.BOX_FONT, PDFPage.RIGHT, PERCENT))
    SUMMARY_BOX_ROW_MARGIN = 10

    DETAILS_BOX_HEADER_COLS = ((50, PDFPage.BOX_FONT_BOLD, PDFPage.LEFT), (350, PDFPage.BOX_FONT_BOLD, PDFPage.LEFT), (85, PDFPage.BOX_FONT_BOLD, PDFPage.LEFT), (100, PDFPage.BOX_FONT_BOLD, PDFPage.RIGHT))
    DETAILS_BOX_CATEGORY_COLS = ((50, PDFPage.BOX_FONT_BOLD, PDFPage.LEFT), (535, PDFPage.BOX_FONT_BOLD, PDFPage.LEFT))
    DETAILS_BOX_ROW_COLS = ((50, PDFPage.BOX_FONT, PDFPage.LEFT), (350, PDFPage.BOX_FONT, PDFPage.LEFT), (85, PDFPage.BOX_FONT, PDFPage.LEFT), (100, PDFPage.BOX_FONT_BOLD, PDFPage.RIGHT))
    DETAILS_BOX_ROW_MARGIN = 10

    TNS_LOGO = os.path.join(settings.RESOURCES_DIR, 'tns_report_logo.png')

    # raw image is 194x36, aspect ratio should be maintained with whatever we set here
    TNS_LOGO_HEIGHT = 18.5
    TNS_LOGO_WIDTH = 100

    # raw image is 519x236, aspect ratio should be maintained with whatever we set here
    AWARD_HEIGHT = 92
    AWARD_WIDTH = 200
    
    def __init__(self, scorecard, show_summary=False):
        self.scorecard = scorecard
        self.show_summary = show_summary

        activate('en_us')

        self.calculate_metrics()

    def calculate_metrics(self):
        self.HEADER_ASCENT = getAscent(self.HEADER_FONT, self.HEADER_SIZE)
        self.HEADER_DESCENT = -getDescent(self.HEADER_FONT, self.HEADER_SIZE)
        self.HEADER_HEIGHT = self.HEADER_ASCENT + self.HEADER_DESCENT + self.HEADER_PADDING * 2

        self.BOX_ASCENT = getAscent(self.BOX_FONT, self.BOX_SIZE)
        self.BOX_DESCENT = -getDescent(self.BOX_FONT, self.BOX_SIZE)
        self.BOX_HEIGHT = self.BOX_ASCENT + self.BOX_DESCENT + self.BOX_PADDING * 2

        self.SUMMARY_BOX_WIDTH = self.WIDTH - self.PAGE_MARGIN * 2


    def draw_header(self, c, y, left, right=None):

        # set the rect background color
        self.set_black(c)
        c.rect(self.PAGE_MARGIN, y, self.WIDTH-self.PAGE_MARGIN*2, self.HEADER_HEIGHT, fill=True)

        # set the text foreground color
        self.set_white(c)
        self.set_font(c, self.HEADER_FONT, self.HEADER_SIZE)
        
        y += self.HEADER_PADDING + self.HEADER_ASCENT

        c.drawString(self.PAGE_MARGIN+self.HEADER_PADDING, y, left)

        if right:
            c.drawRightString(self.WIDTH-self.PAGE_MARGIN-self.HEADER_PADDING, y, right)

        return self.HEADER_HEIGHT

    def draw_centered_box(self, c, x, y, width, header):
        self.set_black(c)
        c.rect(x, y, width, self.BOX_HEIGHT, fill=1)

        self.set_white(c)
        self.set_font(c, self.BOX_FONT_BOLD, self.BOX_SIZE)

        y += self.BOX_PADDING + self.BOX_ASCENT
        c.drawCentredString(x + width / 2, y, header)

        return self.BOX_HEIGHT + self.BOX_PADDING

    def format_value(self, value, format):
        if value is None: # pragma: no cover
            return ""

        if format == self.PERCENT:
            return str(value) + '%'
        else:
            return str(value)

    def draw_scorecard_details(self, c, y):
        top_y = y
        x = self.PAGE_MARGIN

        self.set_black(c)
        client_id = self.scorecard.client_id if self.scorecard.client_id else 'N/A'        
        y += self.draw_row(c, x, y+self.get_ascent(), self.AUDIT_ROW_COLS, (_("Client ID"), client_id))

        # draw the auditor
        if self.scorecard.auditor:
            y += self.draw_row(c, x, y+self.get_ascent(), self.AUDIT_ROW_COLS, (_("Auditor"), self.scorecard.auditor))

        # draw the audit date
        if self.scorecard.audit_date:
            y += self.draw_row(c, x, y+self.get_ascent(), self.AUDIT_ROW_COLS, (_("Audit Date"), self.scorecard.audit_date.strftime("%B %d, %Y")))

        # draw the scorecard reporting date
        if self.scorecard.modified_on:
            y += self.draw_row(c, x, y+self.get_ascent(), self.AUDIT_ROW_COLS, (_("Report Date"), self.scorecard.modified_on.strftime("%B %d, %Y")))

        return y - top_y

    def draw_tns_logo(self, c, x, y):
        c.saveState()
        c.translate(x, y+self.TNS_LOGO_HEIGHT)
        c.scale(1.0,-1.0)
        (width, height) = c.drawImage(self.TNS_LOGO, 0, 0, 
                                      width=self.TNS_LOGO_WIDTH, height=self.TNS_LOGO_HEIGHT,
                                      mask='auto', preserveAspectRatio=True, anchor='nw')
        c.restoreState()
        return self.TNS_LOGO_HEIGHT

    def draw_scorecard_award(self, c, y, award):
        c.saveState()
        c.translate(self.WIDTH-self.PAGE_MARGIN-self.AWARD_WIDTH, y+self.AWARD_HEIGHT)
        c.scale(1.0,-1.0)
        award_file_name = '%s.png' % award
        (width, height) = c.drawImage(os.path.join(settings.RESOURCES_DIR, award_file_name), 0, 0, 
                                      width=self.AWARD_WIDTH, height=self.AWARD_HEIGHT,
                                      mask='auto', preserveAspectRatio=True, anchor='nw')
        c.restoreState()
        return self.AWARD_HEIGHT

    def draw_summary_box(self, c, y):
        width = self.SUMMARY_BOX_WIDTH
        top_y = y

        x = self.PAGE_MARGIN
        y += self.draw_box_header(c, x, y, _("Sustainability Standards Scorecard Summary"), self.SUMMARY_BOX_HEADER_COLS,
                                  (_("Standard Categories"), _("All Minimum Requirements Met?"), _("Best Practice with Full Compliance (%)")))

        for category in self.scorecard.season.get_standard_categories():
            category_summary = self.scorecard.calculate_metrics()[category.acronym]

            y += self.draw_row(c, x, y, self.SUMMARY_BOX_CATEGORY_COLS, (category.name, category_summary[0], str(category_summary[1])))
            y += self.BOX_PADDING
        
        y -= self.BOX_PADDING
        c.rect(x, top_y, width, y - top_y)

        y += self.SECTION_MARGIN

        return y - top_y

    def draw_summary_bar_graph(self, c, y, height):

        BAR_WIDTH = 50
        BAR_SPACING = 40

        TICKED_SIZE = 30

        x = self.PAGE_MARGIN*2
        width = self.WIDTH - x
        bar_height = height - self.PAGE_MARGIN*2
        mid_height = bar_height/2

        # draw the title
        self.set_black(c)
        c.drawString(x, y + mid_height, _("Best Practice with Full Compliance (%)"))

        graph_x = x + self.get_width("Best Practice with Full Compliance (%)") + self.PAGE_MARGIN

        all_category_heights = []
        scorecard_metrics = self.scorecard.calculate_metrics()
        for count, category in enumerate(self.scorecard.season.get_standard_categories()):

            if count == 0:
                c.line(graph_x, y+bar_height, graph_x+x, y+bar_height)

            # decide the length of the bar
            bar_length = (bar_height * scorecard_metrics[category.acronym][1]) / 100
            diff = bar_length - bar_height 

            # draw the bar
            c.rect(graph_x+self.PAGE_MARGIN*2, y-diff, BAR_WIDTH, bar_length, fill=True)

            # draw the category name under the bar
            self.set_font(c, self.BOX_FONT, self.BOX_SIZE)
            category_height = self.wrap_word(c, graph_x, y+bar_height+self.PAGE_MARGIN*2,BAR_WIDTH+self.PAGE_MARGIN*4, 'center', category.name)

            all_category_heights.append(category_height)

            max_height = max(all_category_heights)
            
            # draw the line 
            graph_x += BAR_WIDTH + BAR_SPACING

            if count >= 0 and count < len(scorecard_metrics)-1:
                c.line(graph_x+x, y+bar_height, graph_x-BAR_SPACING, y+bar_height)
            else:
                c.line(graph_x-BAR_SPACING+x, y+bar_height, graph_x-BAR_SPACING+x*2, y+bar_height)

            # then after draw the image related to the minimum requirement fullfilment
            if scorecard_metrics[category.acronym][0] == 'YES':
                file_name = 'ticked.png'
            elif scorecard_metrics[category.acronym][0] == 'NO':
                file_name = 'unticked.png'
            else:
                file_name = 'na.png'
            
            c.drawImage(os.path.join(settings.RESOURCES_DIR, file_name), graph_x-BAR_WIDTH-TICKED_SIZE/2, y+bar_height+max_height+self.PAGE_MARGIN*2, 
                                      width=TICKED_SIZE, height=TICKED_SIZE,
                                      mask='auto', preserveAspectRatio=True, anchor='c')

            # in the bar draw its value in percentage
            if -diff > bar_height/3:
                self.set_black(c)
                c.drawCentredString(graph_x-BAR_WIDTH-self.PAGE_MARGIN, y-diff-self.PAGE_MARGIN*2, self.format_value(scorecard_metrics[category.acronym][1], self.PERCENT))
            else:
                self.set_white(c)
                c.drawCentredString(graph_x-BAR_WIDTH-self.PAGE_MARGIN, y-diff+self.PAGE_MARGIN*2, self.format_value(scorecard_metrics[category.acronym][1], self.PERCENT))

            # draw the all minimum section title
            self.set_black(c)

        self.set_font(c, self.BOX_FONT_BOLD, self.BOX_SIZE)
        c.drawString(x, y+height+max_height + TICKED_SIZE/2, _("All Minimum Requirement Met?"))

        return height + max_height + TICKED_SIZE
        
    def draw_summary_graph_box(self, c, y):
        HEIGHT = 300
        width = self.SUMMARY_BOX_WIDTH
        top_y = y

        x = self.PAGE_MARGIN
        y += self.draw_centered_box(c, x, y, width, _("Sustainability Standards Scorecard Summary Graph"))

        # maintain the y position for the graph
        graph_y = y
        
        # draw the graph
        y += self.PAGE_MARGIN
        y += self.draw_summary_bar_graph(c, y, HEIGHT) + self.PAGE_MARGIN

        c.rect(x, top_y, width, y - top_y)

        y += self.SECTION_MARGIN

        return y - top_y

    def format_compliance_to_string(self, standard):
        if len(standard.standard_entries.all()) > 0:
            value = self.scorecard.standard_entries.get(standard=standard).value
        else:
            value = -1

        if standard.kind == 'MR':
            if value > 0:
                return "PASS"
            elif value == 0:
                return "FAIL"
            else:
                return '-'
        else:
            if value >= 0:
                return str(value) + '%'
            else:
                return '-'

    def draw_standard_details_box(self, c, y):
        #self.BOX_PADDING = 3
        self.CATEGORY_FONT_SIZE = 7
        width = self.SUMMARY_BOX_WIDTH

        x = self.PAGE_MARGIN
        y += self.draw_centered_box(c, x, y, self.WIDTH-self.PAGE_MARGIN*2, _("Sustainability Standards Scorecard Details"))

        top_y = y        

        self.set_black(c)
        c.rect(x,y, self.WIDTH-self.PAGE_MARGIN*2, self.get_line_height()+self.get_ascent(), fill=True)
        y += self.BOX_PADDING

        self.set_white(c)
        y += self.draw_row(c, x, y, self.DETAILS_BOX_ROW_COLS, (_("ID"), _("Standard"), _("Type"), _("Compliance")))
        self.set_black(c)
        y += self.PAGE_MARGIN
        season = self.scorecard.season

        for count, category in enumerate(season.get_standard_categories()):
            # draw the category row
            y += self.draw_row(c, x, y, self.DETAILS_BOX_CATEGORY_COLS, (category.acronym, category.name), size=self.CATEGORY_FONT_SIZE)
            c.line(self.PAGE_MARGIN,y,self.WIDTH-self.PAGE_MARGIN, y)
            y += self.get_ascent()
            
            for standard in season.get_standards(category=category):
                # draw the standard row
                y += self.draw_row(c, x, y, self.DETAILS_BOX_ROW_COLS, (standard.acronym(), standard.name, standard.get_kind_display(), self.format_compliance_to_string(standard)))

            if count != len(season.get_standard_categories())-1:
                c.line(self.PAGE_MARGIN,y,self.WIDTH-self.PAGE_MARGIN, y)
                y += self.get_ascent()

        c.rect(x, top_y, width, y - top_y)

        y += self.PAGE_MARGIN + self.get_line_height()
        return y - top_y

    def draw_page_one(self, c, metrics):
        # start the page
        current_x = self.PAGE_MARGIN 
        current_y = self.PAGE_MARGIN * 3

        # our main header
        current_y += self.draw_header(c, current_y, 
                                      _("%s (%s)") % (self.scorecard.wetmill.name, self.scorecard.wetmill.country.name), 
                                      _("%s Sustainability Standards Scorecard Sheet") % self.scorecard.season.name)

        current_y += self.SECTION_MARGIN

        # draw scorecard details
        left_height = current_y + self.draw_tns_logo(c, self.PAGE_MARGIN, current_y+self.PAGE_MARGIN*2) + self.PAGE_MARGIN*4
        left_height += self.draw_scorecard_details(c, left_height)
        right_height = current_y + self.draw_scorecard_award(c, current_y, self.scorecard.get_rating())

        # get the new postioning depending on which of both left and right
        current_y = max(left_height, right_height) + self.PAGE_MARGIN

        # draw the summary box
        current_y += self.draw_summary_box(c, current_y)

        # draw the bar graph
        current_y += self.draw_summary_graph_box(c, current_y)

        # draw generated on
        self.draw_generated_on(c, current_y)

    def draw_page_two(self, c):
        c.showPage()
        # start the page
        current_x = self.PAGE_MARGIN 
        current_y = self.PAGE_MARGIN * 3

        # our main header
        current_y += self.draw_header(c, current_y, 
                                      _("%s (%s)") % (self.scorecard.wetmill.name, self.scorecard.wetmill.country.name), 
                                      _("%s Sustainability Standards Scorecard Sheet") % self.scorecard.season.name)

        current_y += self.SECTION_MARGIN

        # draw scorecard details
        right_height = self.draw_tns_logo(c, self.WIDTH - self.TNS_LOGO_WIDTH - self.PAGE_MARGIN, current_y+self.PAGE_MARGIN*2)
        left_height = self.draw_scorecard_details(c, current_y)

        # get the new postioning depending on which of both left and right
        current_y += max(left_height, right_height) + self.PAGE_MARGIN

        # draw the summary box
        current_y += self.draw_standard_details_box(c, current_y) + self.PAGE_MARGIN

        # draw generated on
        self.draw_generated_on(c, current_y)

    def render(self, output_buffer):
        # Create the PDF object, using the StringIO object as its "file."
        c = self.create_canvas(output_buffer)

        # decide weither to show or to hide the summary page
        # based on the fact if the scorecard has been finalized or not.
        self.show_summary = self.scorecard.is_finalized
            
        if self.show_summary:
            self.draw_page_one(c, self.scorecard.calculate_metrics())

        self.draw_page_two(c)

        c.save()
        return output_buffer
