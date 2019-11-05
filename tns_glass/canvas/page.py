import os
from datetime import datetime

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth, getAscent, getDescent

from django.conf import settings
from django.utils.translation import ugettext as _

class PDFPage(object):

    PAGE_WIDTH = A4[0]
    PAGE_HEIGHT = A4[1]

    SPEC_WIDTH = 0
    SPEC_FONT = 1
    SPEC_ALIGNMENT = 2
    SPEC_FORMAT = 3
    SPEC_TRANSFORM = 4

    HEADER_FONT = "Helvetica-Bold"
    HEADER_SIZE = 9
    HEADER_PADDING = 5
    HEADER_ASCENT = 0
    HEADER_DESCENT = 0
    HEADER_HEIGHT = 0
    
    BOX_FONT_BOLD = "Helvetica-Bold"
    BOX_FONT = "Helvetica"
    BOX_ITALIC = "Helvetica-Oblique"
    BOX_SIZE = 6
    BOX_PADDING = 3
    BOX_ASCENT = 0
    BOX_DESCENT = 0
    BOX_HEIGHT = 0
    BOX_PADDING = 4

    LEFT = 0
    CENTER = 1
    RIGHT = 2

    RAW = -1

    LOCAL = 0
    LOCAL_EVEN = 1
    USD = 2
    USD_EVEN = 3
    CURR = 4
    CURR_EVEN = 5
    EVEN = 7
    DECIMAL = 8
    CURR_CONVERT = 9
    WEIGHT = 10


    PER_WEIGHT_UNIT_CHERRY = 1
    PER_WEIGHT_UNIT_GREEN = 2
    AGGREGATE_AVERAGE = 3
    AGGREGATE_BEST = 4
    PER_GREEN_RATIO = 5
    PER_WEIGHT_KILO = 6

    WIDTH, HEIGHT = A4
    PAGE_MARGIN = 5
    SECTION_MARGIN = 5

    def set_font_size(self, size):
        return size
    
    def set_font(self, c, font, size):
        self.font = font
        self.size = size
        c.setFont(font, size)

    def set_black(self, c):
        c.setFillColorRGB(0, 0, 0)

    def set_white(self, c):
        c.setFillColorRGB(255, 255, 255)

    def break_into_lines(self, label, width):
        lines = []
        remainder = ""

        # if there is no label
        if label is None:
            # convert label to empty string to prevent a crazy crush just for the graph
            label = ""

        # remove any trailing space
        label = label.strip()

        # calculate the string width
        length = self.get_width(label)

        # if the string exceeds the width
        if length > width:
            # look for space
            # if the string contains space
            if label.find(' ') != -1:
                # divide the string into pieces that doesn't exceed the width
                words = label.split()
                section = ''

                num = 0
                # loop into words strings
                for (counter, string) in enumerate(words):

                    # combine them without exceeding the width
                    if self.get_width(section + string + " ") < width:
                        section = section + string + " "
                        num = counter+1
                    else:
                        break

                lines.append(section)

                remainder = " ".join(words[num:])

            else:
                line = label
                while self.get_width(line+"-") > width:
                    line = line[:-1]
                    
                lines.append(line+"-")
                length = len(line)
                remainder = label[length:]

            if remainder:
                if self.get_width(remainder) <= width:
                    lines.append(remainder)
                else:
                    while self.get_width(remainder + "..") > width:
                        remainder = remainder[:-1]
                
                    lines.append(remainder+"..")
        else:
            lines.append(label)

        return lines

    def wrap_word(self,c, x, y, width, position, label):
        """
        Given the width of the string length draw lookup for space and break the line
        """
        top_y = y
        lines = self.break_into_lines(label, width)

        for line in lines:
            if position == 'center':
                c.drawCentredString(x+width/2, y+self.get_ascent(), line.strip())
            elif position == 'right':
                c.drawRightString(x+width, y+self.get_ascent(), line.strip())
            else:
                c.drawString(x, y+self.get_ascent(), line.strip())

            y += self.get_line_height()

        return y - top_y

    def draw_header(self, c, y, left, right=None):
        self.set_black(c)
        c.rect(self.PAGE_MARGIN, y, self.WIDTH-self.PAGE_MARGIN*2, self.HEADER_HEIGHT, fill=1)

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

    def get_line_height(self):
        return getAscent(self.font, self.size) - getDescent(self.font, self.size) + self.BOX_PADDING

    def get_ascent(self):
        return getAscent(self.font, self.size)

    def get_width(self, text):
        return stringWidth(text, self.font, self.size)

    def format_value(self, value, format, exchange):
        if exchange is None:
            exchange = self.exchange

        if value is None:
            return " "

        if value == "-":
            return " "

        if format == self.LOCAL:
            return self.local_currency.format(value.as_local(exchange))

        elif format == self.CURR_CONVERT:
            if self.report_currency == self.usd:
                value = value / exchange
            return self.report_currency.format(value)

        elif format == self.CURR:
            if self.report_currency == self.usd:
                value = value.as_usd(exchange)
            else:
                value = value.as_local(exchange)
            return self.report_currency.format(value)

        elif format == self.CURR_EVEN:
            if self.report_currency == self.usd:
                value = value.as_usd(exchange)
            else:
                value = value.as_local(exchange)
            return self.report_currency.format(value, force_even=True)

        elif format == self.WEIGHT:
            return self.report_weight.format(value, True)

        elif format == self.EVEN:
            return self.decimal_to_string(value, True)

        elif format == self.DECIMAL:
            return self.decimal_to_string(value)

        else:
            return str(value)

    def draw_row(self, c, x, y, cols, vals, size=BOX_SIZE):
        height = self.get_line_height()

        for (i, value) in enumerate(vals):
            if len(cols[i]) > self.SPEC_TRANSFORM:
                value = self.transform_value(value, cols[i][self.SPEC_TRANSFORM])

            if len(cols[i]) > self.SPEC_FORMAT:
                value = self.format_value(value, cols[i][self.SPEC_FORMAT], self.exchange)

            self.set_font(c, cols[i][self.SPEC_FONT], size)
            alignment = cols[i][self.SPEC_ALIGNMENT]

            if value is None:  # pragma: no cover
                value = ""

            lines = self.break_into_lines(value, cols[i][self.SPEC_WIDTH])
            height = max(len(lines) * self.get_line_height(), height)
            line_y = y + self.get_ascent()

            for line in lines:
                if alignment == self.LEFT:
                    draw_x = x
                    if i == 0:
                        draw_x += self.BOX_PADDING
                    c.drawString(draw_x, line_y, line)

                elif alignment == self.RIGHT:
                    if i+1 == len(vals):
                        x -= self.BOX_PADDING
                    c.drawRightString(x+cols[i][self.SPEC_WIDTH], line_y, line)

                else:
                    c.drawCentredString(x+cols[i][self.SPEC_WIDTH]/2, line_y, line)

                line_y += self.get_line_height()

            x += cols[i][self.SPEC_WIDTH]

        return height

    def draw_row_historical(self, c, x, y, cols, vals, exchange_one_season_ago, exchange_two_seasons_ago, size=BOX_SIZE):
        """
        This is different from the draw_row because it doesn't just use the current season's exchange rate.
        Instead, it takes historical seasons as input as well and uses the different exchange rates when calculating historical values.
        If draw_row is used for historical calculations, it will give the error that old seasons would use present season exchange rate.
        """
        height = self.get_line_height()

        for (i, value) in enumerate(vals):
            if len(cols[i]) > self.SPEC_TRANSFORM:
                value = self.transform_value(value, cols[i][self.SPEC_TRANSFORM])

            if len(cols[i]) > self.SPEC_FORMAT:
                exchange = self.exchange
                """
                The format of cols[i] is [Local Sales   Value_two_Seasons_Ago   Value_One_Season_Ago    Value_Current_Season]
                So, if i = 1, we set the season equal to the value two seasons ago
                if i = 2, we set the season equal to the value one season ago
                The season is important because the exchange rate differs season by season.
                """
                if i == 1:
                    exchange = exchange_two_seasons_ago
                if i == 2:
                    exchange = exchange_one_season_ago

                value = self.format_value(value, cols[i][self.SPEC_FORMAT], exchange)

            self.set_font(c, cols[i][self.SPEC_FONT], size)
            alignment = cols[i][self.SPEC_ALIGNMENT]

            if value is None:  # pragma: no cover
                value = ""

            lines = self.break_into_lines(value, cols[i][self.SPEC_WIDTH])
            height = max(len(lines) * self.get_line_height(), height)
            line_y = y + self.get_ascent()

            for line in lines:
                if alignment == self.LEFT:
                    draw_x = x
                    if i == 0:
                        draw_x += self.BOX_PADDING
                    c.drawString(draw_x, line_y, line)

                elif alignment == self.RIGHT:
                    if i+1 == len(vals):
                        x -= self.BOX_PADDING
                    c.drawRightString(x+cols[i][self.SPEC_WIDTH], line_y, line)

                else:
                    c.drawCentredString(x+cols[i][self.SPEC_WIDTH]/2, line_y, line)

                line_y += self.get_line_height()

            x += cols[i][self.SPEC_WIDTH]

        return height

    def draw_box_header(self, c, x, y, header, header_cols, header_vals):
        width = 0
        for col in header_cols:
            width += col[0]

        height = self.draw_centered_box(c, x, y, width, header)
        
        self.set_black(c)
        if header_vals:
            height += self.draw_row(c, x, y+height, header_cols, header_vals)
            c.rect(x, y, width, height)
            height += self.BOX_PADDING

        return height

    def draw_generated_on(self, c, y):
        y += self.SECTION_MARGIN + 2
        x = self.PAGE_MARGIN * 2
        self.set_font(c, self.BOX_ITALIC, self.BOX_SIZE)
        c.drawRightString(self.WIDTH - x, y, _("Generated on %s") % str(datetime.now().strftime("%A, %d. %B %Y at %I:%M%p GMT")))

    def create_canvas(self, output_buffer):
        # create our canvas
        c = canvas.Canvas(output_buffer, pagesize=A4, bottomup=0)

        # set our font to our defaults
        self.set_font(c, self.BOX_FONT, self.BOX_SIZE)

        # and return it
        return c

    def draw_tns_logo(self, c, y):
        c.saveState()
        c.translate(self.WIDTH-self.PAGE_MARGIN-self.TNS_LOGO_WIDTH, y+self.TNS_LOGO_HEIGHT)
        c.scale(1.0,-1.0)
        (width, height) = c.drawImage(self.TNS_LOGO, 0, 0, 
                                      width=self.TNS_LOGO_WIDTH, height=self.TNS_LOGO_HEIGHT,
                                      mask='auto', preserveAspectRatio=True, anchor='nw')
        c.restoreState()
