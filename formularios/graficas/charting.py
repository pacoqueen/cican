# - coding: utf-8 -

# Copyright (C) 2008-2010 Toms Bauģis <toms.baugis at gmail.com>

# This file is part of Project Hamster.

# Project Hamster is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Project Hamster is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Project Hamster.  If not, see <http://www.gnu.org/licenses/>.


##############################################################################
# Modificado por Francisco José Rodríguez Bogado. (pacoqueen@users.sf.net)   #
##############################################################################

import gtk, gobject
import pango
import datetime as dt
import time
import graphics, stuff
import locale
import colorsys
from sys import maxint


class Bar(graphics.Sprite):
    def __init__(self, key, value, normalized, label_color):
        graphics.Sprite.__init__(self, cache_as_bitmap=True)
        self.key, self.value, self.normalized = key, value, normalized

        self.height = 0
        self.width = 20
        self.interactive = True
        self.fill = None

        self.label = graphics.Label(value, size=8, color=label_color)
        self.label_background = graphics.Rectangle(self.label.width + 4, self.label.height + 4, 4, visible=False)
        self.add_child(self.label_background)
        self.add_child(self.label)
        self.connect("on-render", self.on_render)

    def on_render(self, sprite):
        # invisible rectangle for the mouse, covering whole area
        self.graphics.rectangle(0, 0, self.width, self.height)
        self.graphics.fill("#000", 0)

        size = round(self.width * self.normalized)

        self.graphics.rectangle(0, 0, size, self.height, 3)
        self.graphics.rectangle(0, 0, min(size, 3), self.height)
        self.graphics.fill(self.fill)

        self.label.y = (self.height - self.label.height) / 2

        horiz_offset = min(10, self.label.y * 2)

        if self.label.width < size - horiz_offset * 2:
            #if it fits in the bar
            self.label.x = size - self.label.width - horiz_offset
        else:
            self.label.x = size + 3

        self.label_background.x = self.label.x - 2
        self.label_background.y = self.label.y - 2


class Chart(graphics.Scene):
    __gsignals__ = {
        "bar-clicked": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, )),
    }

    def __init__(self, max_bar_width = 20, legend_width = 70, value_format = "%.2f", interactive = True):
        graphics.Scene.__init__(self)

        self.selected_keys = [] # keys of selected bars

        self.bars = []
        self.labels = []
        self.data = None

        self.max_width = max_bar_width
        self.legend_width = legend_width
        self.value_format = value_format
        self.graph_interactive = interactive

        self.plot_area = graphics.Sprite(interactive = False)
        self.add_child(self.plot_area)

        self.bar_color, self.label_color = None, None

        self.connect("on-enter-frame", self.on_enter_frame)

        if self.graph_interactive:
            self.connect("on-mouse-over", self.on_mouse_over)
            self.connect("on-mouse-out", self.on_mouse_out)
            self.connect("on-click", self.on_click)

    def find_colors(self):
        bg_color = self.get_style().bg[gtk.STATE_NORMAL].to_string()
        self.bar_color = self.colors.contrast(bg_color, 30)

        # now for the text - we want reduced contrast for relaxed visuals
        fg_color = self.get_style().fg[gtk.STATE_NORMAL].to_string()
        self.label_color = self.colors.contrast(fg_color,  80)


    def on_mouse_over(self, scene, bar):
        if bar.key not in self.selected_keys:
            bar.fill = self.get_style().base[gtk.STATE_PRELIGHT].to_string()

    def on_mouse_out(self, scene, bar):
        if bar.key not in self.selected_keys:
            bar.fill = self.bar_color

    def on_click(self, scene, event, clicked_bar):
        if not clicked_bar: return
        self.emit("bar-clicked", clicked_bar.key)

    def plot(self, keys, data):
        self.data = data

        bars = dict([(bar.key, bar.normalized) for bar in self.bars])

        max_val = float(max(data or [0]))

        new_bars, new_labels = [], []
        for key, value in zip(keys, data):
            if max_val:
                normalized = value / max_val
            else:
                normalized = 0
            bar = Bar(key, locale.format(self.value_format, value), normalized, self.label_color)
            bar.interactive = self.graph_interactive

            if key in bars:
                bar.normalized = bars[key]
                self.tweener.add_tween(bar, normalized=normalized)
            new_bars.append(bar)

            label = graphics.Label(stuff.escape_pango(key), size = 8, alignment = pango.ALIGN_RIGHT)
            new_labels.append(label)


        self.plot_area.remove_child(*self.bars)
        self.remove_child(*self.labels)

        self.bars, self.labels = new_bars, new_labels
        self.add_child(*self.labels)
        self.plot_area.add_child(*self.bars)

        self.show()
        self.redraw()


    def on_enter_frame(self, scene, context):
        # adjust sizes and positions on redraw

        legend_width = self.legend_width
        if legend_width < 1: # allow fractions
            legend_width = int(self.width * legend_width)

        self.find_colors()

        self.plot_area.y = 0
        self.plot_area.height = self.height - self.plot_area.y
        self.plot_area.x = legend_width + 8
        self.plot_area.width = self.width - self.plot_area.x

        y = 0
        for i, (label, bar) in enumerate(zip(self.labels, self.bars)):
            bar_width = min(round((self.plot_area.height - y) / (len(self.bars) - i)), self.max_width)
            bar.y = y
            bar.height = bar_width
            bar.width = self.plot_area.width

            if bar.key in self.selected_keys:
                bar.fill = self.get_style().bg[gtk.STATE_SELECTED].to_string()

                if bar.normalized == 0:
                    bar.label.color = self.get_style().fg[gtk.STATE_SELECTED].to_string()
                    bar.label_background.fill = self.get_style().bg[gtk.STATE_SELECTED].to_string()
                    bar.label_background.visible = True
                else:
                    bar.label_background.visible = False
                    if bar.label.x < round(bar.width * bar.normalized):
                        bar.label.color = self.get_style().fg[gtk.STATE_SELECTED].to_string()
                    else:
                        bar.label.color = self.label_color

            if not bar.fill:
                bar.fill = self.bar_color

                bar.label.color = self.label_color
                bar.label_background.fill = None

            label.y = y + (bar_width - label.height) / 2 + self.plot_area.y

            label.width = legend_width
            if not label.color:
                label.color = self.label_color

            y += bar_width + 1


class HorizontalDayChart(graphics.Scene):
    """Pretty much a horizontal bar chart, except for values it expects tuple
    of start and end time, and the whole thing hangs in air"""
    def __init__(self, max_bar_width, legend_width):
        graphics.Scene.__init__(self)
        self.max_bar_width = max_bar_width
        self.legend_width = legend_width
        self.start_time, self.end_time = None, None
        self.connect("on-enter-frame", self.on_enter_frame)

    def plot_day(self, keys, data, start_time = None, end_time = None):
        self.keys, self.data = keys, data
        self.start_time, self.end_time = start_time, end_time
        self.show()
        self.redraw()

    def on_enter_frame(self, scene, context):
        g = graphics.Graphics(context)

        rowcount, keys = len(self.keys), self.keys

        start_hour = 0
        if self.start_time:
            start_hour = self.start_time
        end_hour = 24 * 60
        if self.end_time:
            end_hour = self.end_time


        # push graph to the right, so it doesn't overlap
        legend_width = self.legend_width or self.longest_label(keys)

        self.graph_x = legend_width
        self.graph_x += 8 #add another 8 pixes of padding

        self.graph_width = self.width - self.graph_x

        # TODO - should handle the layout business in graphics
        self.layout = context.create_layout()
        default_font = pango.FontDescription(self.get_style().font_desc.to_string())
        default_font.set_size(8 * pango.SCALE)
        self.layout.set_font_description(default_font)


        #on the botttom leave some space for label
        self.layout.set_text("1234567890:")
        label_w, label_h = self.layout.get_pixel_size()

        self.graph_y, self.graph_height = 0, self.height - label_h - 4

        if not self.data:  #if we have nothing, let's go home
            return


        positions = {}
        y = 0
        bar_width = min(self.graph_height / float(len(self.keys)), self.max_bar_width)
        for i, key in enumerate(self.keys):
            positions[key] = (y + self.graph_y, round(bar_width - 1))

            y = y + round(bar_width)
            bar_width = min(self.max_bar_width,
                            (self.graph_height - y) / float(max(1, len(self.keys) - i - 1)))



        max_bar_size = self.graph_width - 15


        # now for the text - we want reduced contrast for relaxed visuals
        fg_color = self.get_style().fg[gtk.STATE_NORMAL].to_string()
        label_color = self.colors.contrast(fg_color,  80)

        self.layout.set_alignment(pango.ALIGN_RIGHT)
        self.layout.set_ellipsize(pango.ELLIPSIZE_END)

        # bars and labels
        self.layout.set_width(legend_width * pango.SCALE)

        factor = max_bar_size / float(end_hour - start_hour)

        # determine bar color
        bg_color = self.get_style().bg[gtk.STATE_NORMAL].to_string()
        base_color = self.colors.contrast(bg_color,  30)

        for i, label in enumerate(keys):
            g.set_color(label_color)

            self.layout.set_text(label)
            label_w, label_h = self.layout.get_pixel_size()

            context.move_to(0, positions[label][0] + (positions[label][1] - label_h) / 2)
            context.show_layout(self.layout)

            if isinstance(self.data[i], list) == False:
                self.data[i] = [self.data[i]]

            for row in self.data[i]:
                bar_x = round((row[0]- start_hour) * factor)
                bar_size = round((row[1] - start_hour) * factor - bar_x)

                g.fill_area(round(self.graph_x + bar_x),
                              positions[label][0],
                              bar_size,
                              positions[label][1],
                              base_color)

        #white grid and scale values
        self.layout.set_width(-1)

        context.set_line_width(1)

        pace = ((end_hour - start_hour) / 3) / 60 * 60
        last_position = positions[keys[-1]]


        grid_color = self.get_style().bg[gtk.STATE_NORMAL].to_string()

        for i in range(start_hour + 60, end_hour, pace):
            x = round((i - start_hour) * factor)

            minutes = i % (24 * 60)

            self.layout.set_markup(dt.time(minutes / 60, minutes % 60).strftime("%H<small><sup>%M</sup></small>"))
            label_w, label_h = self.layout.get_pixel_size()

            context.move_to(self.graph_x + x - label_w / 2,
                            last_position[0] + last_position[1] + 4)
            g.set_color(label_color)
            context.show_layout(self.layout)


            g.set_color(grid_color)
            g.move_to(round(self.graph_x + x) + 0.5, self.graph_y)
            g.line_to(round(self.graph_x + x) + 0.5,
                                 last_position[0] + last_position[1])


        context.stroke()

## Cosas del antiguo charting

def size_list(set, target_set):
    """turns set lenghts into target set - trim it, stretches it, but
       keeps values for cases when lengths match
    """
    set = set[:min(len(set), len(target_set))] #shrink to target
    set += target_set[len(set):] #grow to target

    #nest
    for i in range(len(set)):
        if isinstance(set[i], list):
            set[i] = size_list(set[i], target_set[i])
    return set

def get_limits(set, stack_subfactors = True):
    # stack_subfactors indicates whether we should sum up nested lists
    max_value, min_value = -maxint, maxint
    for col in set:
        if type(col) in [int, float]:
            max_value = max(col, max_value)
            min_value = min(col, min_value)
        elif stack_subfactors:
            max_value = max(sum(col), max_value)
            min_value = min(sum(col), min_value)
        else:
            for row in col:
                max_value = max(row, max_value)
                min_value = max(row, min_value)

    return min_value, max_value


class OldChart(graphics.Area):  # Chart pero en ye olde ztyle
    """Chart constructor. Optional arguments:
        self.max_bar_width     = pixels. Maximal width of bar. If not specified,
                                 bars will stretch to fill whole area
        self.legend_width      = pixels. Legend width will keep you graph
                                 from floating around.
        self.animate           = Should transitions be animated.
                                 Defaults to TRUE
        self.framerate         = Frame rate for animation. Defaults to 60

        self.background        = Tripplet-tuple of background color in RGB
        self.chart_background  = Tripplet-tuple of chart background color in RGB
        self.bar_base_color    = Tripplet-tuple of bar color in RGB

        self.show_scale        = Should we show scale values. See grid_stride!
        self.grid_stride       = Step of grid. If expressed in normalized range
                                 (0..1), will be treated as percentage.
                                 Otherwise will be striding through maximal value.
                                 Defaults to 0. Which is "don't draw"

        self.values_on_bars    = Should values for each bar displayed on top of
                                 it.
        self.value_format      = Format string for values. Defaults to "%s"

        self.show_stack_labels = If the labels of stack bar chart should be
                                 displayed. Defaults to False
        self.labels_at_end     = If stack bars are displayed, this allows to
                                 show them at right end of graph.
    """
    __gsignals__ = {
        "bar-clicked": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, )), 
    }
    def __init__(self, **args):
        graphics.Area.__init__(self)

        # options
        self.max_bar_width     = args.get("max_bar_width", 500)
        self.legend_width      = args.get("legend_width", 0)
        self.animation           = args.get("animate", True)

        self.background        = args.get("background", None)
        self.chart_background  = args.get("chart_background", None)
        self.bar_base_color    = args.get("bar_base_color", None)

        self.grid_stride       = args.get("grid_stride", None)
        self.values_on_bars    = args.get("values_on_bars", False)
        self.value_format      = args.get("value_format", "%s")
        self.show_scale        = args.get("show_scale", False)

        self.show_stack_labels = args.get("show_stack_labels", False)
        self.labels_at_end     = args.get("labels_at_end", False)
        self.framerate         = args.get("framerate", 60)

        self.interactive       = args.get("interactive", False) # if the bars are clickable

        # other stuff
        self.bars = []
        self.keys = []
        self.data = None
        self.stack_keys = []

        self.key_colors = {} # key:color dictionary. if key's missing will grab basecolor
        self.stack_key_colors = {} # key:color dictionary. if key's missing will grab basecolor


        # use these to mark area where the "real" drawing is going on
        self.graph_x, self.graph_y = 0, 0
        self.graph_width, self.graph_height = None, None

        self.mouse_bar = None
        if self.interactive:
            self.connect("mouse-over", self.on_mouse_over)
            self.connect("button-release", self.on_clicked)

        self.bars_selected = []


    def on_mouse_over(self, area, region):
        if region:
            self.mouse_bar = int(region[0])
        else:
            self.mouse_bar = None

        self.redraw_canvas()

    def on_clicked(self, area, bar):
        self.emit("bar-clicked", self.mouse_bar)

    def select_bar(self, index):
        pass

    def get_bar_color(self, index):
        # returns color darkened by it's index
        # the approach reduces contrast by each step
        base_color = self.bar_base_color or (220, 220, 220)

        base_hls = colorsys.rgb_to_hls(*base_color)

        step = (base_hls[1] - 30) / 10 #will go from base down to 20 and max 22 steps

        return colorsys.hls_to_rgb(base_hls[0],
                                   base_hls[1] - step * index,
                                   base_hls[2])


    def draw_bar(self, x, y, w, h, color = None):
        """ draws a simple bar"""
        base_color = color or self.bar_base_color or (220, 220, 220)
        self.fill_area(x, y, w, h, base_color)


    def plot(self, keys, data, stack_keys = None):
        """Draw chart with given data"""
        self.keys, self.data, self.stack_keys = keys, data, stack_keys

        self.show()

        if not data: #if there is no data, just draw blank
            self.redraw_canvas()
            return


        min, self.max_value = get_limits(data)

        self._update_targets()

        if not self.animation:
            self.tweener.finish()

        self.redraw_canvas()


    def on_expose(self):
        # fill whole area
        if self.background:
            self.fill_area(0, 0, self.width, self.height, self.background)


    def _update_targets(self):
        # calculates new factors and then updates existing set
        max_value = float(self.max_value) or 1 # avoid division by zero

        self.bars = size_list(self.bars, self.data)

        #need function to go recursive
        def retarget(bars, new_values):
            for i in range(len(new_values)):
                if isinstance(new_values[i], list):
                    bars[i] = retarget(bars[i], new_values[i])
                else:
                    if isinstance(bars[i], OldBar) == False:
                        bars[i] = OldBar(new_values[i], 0)
                    else:
                        bars[i].value = new_values[i]
                        self.tweener.kill_tweens(bars[i])

                    self.tweener.add_tween(bars[i], size = bars[i].value / float(max_value))
            return bars

        retarget(self.bars, self.data)


    def longest_label(self, labels):
        """returns width of the longest label"""
        max_extent = 0
        for label in labels:
            self.layout.set_text(label)
            label_w, label_h = self.layout.get_pixel_size()
            max_extent = max(label_w + 5, max_extent)

        return max_extent

    def draw(self):
        logging.error("OMG OMG, not implemented!!!")



class OldBar(object):
    def __init__(self, value, size = 0):
        self.value = value
        self.size = size

    def __repr__(self):
        return str((self.value, self.size))


class BarChart(OldChart):
    def on_expose(self):
        OldChart.on_expose(self)

        if not self.data:
            return

        context = self.context
        context.set_line_width(1)


        # determine graph dimensions
        if self.show_stack_labels:
            legend_width = self.legend_width or self.longest_label(self.keys)
        elif self.show_scale:
            if self.grid_stride < 1:
                grid_stride = int(self.max_value * self.grid_stride)
            else:
                grid_stride = int(self.grid_stride)

            scale_labels = [self.value_format % i
                  for i in range(grid_stride, int(self.max_value), grid_stride)]
            self.legend_width = legend_width = self.legend_width or self.longest_label(scale_labels)
        else:
            legend_width = self.legend_width

        if self.stack_keys and self.labels_at_end:
            self.graph_x = 0
            self.graph_width = self.width - legend_width
        else:
            self.graph_x = legend_width + 8 # give some space to scale labels
            self.graph_width = self.width - self.graph_x - 10

        self.graph_y = 0
        self.graph_height = self.height - 15

        if self.chart_background:
            self.fill_area(self.graph_x, self.graph_y,
                           self.graph_width, self.graph_height,
                           self.chart_background)

        self.context.stroke()

        # bars and keys
        max_bar_size = self.graph_height
        #make sure bars don't hit the ceiling
        if self.animate or self.before_drag_animate:
            max_bar_size = self.graph_height - 10


        prev_label_end = None
        self.layout.set_width(-1)

        exes = {}
        x = 0
        bar_width = min(self.graph_width / float(len(self.keys)), self.max_bar_width)
        for i, key in enumerate(self.keys):
            exes[key] = (x + self.graph_x, round(bar_width - 1))

            x = x + round(bar_width)
            bar_width = min(self.max_bar_width,
                            (self.graph_width - x) / float(max(1, len(self.keys) - i - 1)))


        # now for the text - we want reduced contrast for relaxed visuals
        fg_color = self.get_style().fg[gtk.STATE_NORMAL].to_string()
        if self.colors.is_light(fg_color):
            label_color = self.colors.darker(fg_color,  80)
        else:
            label_color = self.colors.darker(fg_color,  -80)


        for key, bar, data in zip(self.keys, self.bars, self.data):
            self.set_color(label_color);
            self.layout.set_text(key)
            label_w, label_h = self.layout.get_pixel_size()

            intended_x = exes[key][0] + (exes[key][1] - label_w) / 2

            if not prev_label_end or intended_x > prev_label_end:
                self.context.move_to(intended_x, self.graph_height + 4)
                context.show_layout(self.layout)

                prev_label_end = intended_x + label_w + 3


            bar_start = 0

            # determine bar color
            base_color = self.bar_base_color
            if not base_color: #yay, we can be theme friendly!
                bg_color = self.get_style().bg[gtk.STATE_NORMAL].to_string()
                if self.colors.is_light(bg_color):
                    base_color = self.colors.darker(bg_color,  30)
                else:
                    base_color = self.colors.darker(bg_color,  -30)
                    tick_color = self.colors.darker(bg_color,  -50)
                    
            last_color = base_color

            if self.stack_keys:
                remaining_fractions, remaining_pixels = 1, max_bar_size

                for j, stack_bar in enumerate(bar):
                    if stack_bar.size > 0:
                        bar_size = round(remaining_pixels * (stack_bar.size / remaining_fractions))
                        remaining_fractions -= stack_bar.size
                        remaining_pixels -= bar_size

                        bar_start += bar_size
                        last_color = self.stack_key_colors.get(self.stack_keys[j]) or self.get_bar_color(j)
                        self.draw_bar(exes[key][0],
                                      self.graph_height - bar_start,
                                      exes[key][1],
                                      bar_size,
                                      last_color)
            else:
                bar_size = round(max_bar_size * bar.size)
                bar_start = bar_size

                last_color = self.key_colors.get(key) or base_color
                self.draw_bar(exes[key][0],
                              self.graph_y + self.graph_height - bar_size,
                              exes[key][1],
                              bar_size,
                              last_color)


            if self.values_on_bars:  # it is either stack labels or values at the end for now
                if self.stack_keys:
                    # XXX: total_value = sum(data[i])
                    total_value = sum(data)
                else:
                    # XXX: total_value = data[i]
                    total_value = data[data.index(key)]

                self.layout.set_width(-1)
                self.layout.set_text(self.value_format % total_value)
                label_w, label_h = self.layout.get_pixel_size()


                if bar_start > label_h + 2:
                    label_y = self.graph_y + self.graph_height - bar_start + 5
                else:
                    label_y = self.graph_y + self.graph_height - bar_start - label_h + 5

                # XXX: context.move_to(self.exes[key][0] + (self.exes[key][1] - label_w) / 2.0,
                context.move_to(exes[key][0] + (exes[key][1] - label_w) / 2.0,
                                label_y)

                # we are in the bar so make sure that the font color is distinguishable
                if self.colors.is_light(last_color):
                    self.set_color(label_color)
                else:
                    self.set_color(self.colors.almost_white)

                context.show_layout(self.layout)


        #white grid and scale values
        if self.background:
            grid_color = self.background
        else:
            grid_color = self.get_style().bg[gtk.STATE_NORMAL].to_string()
            
        self.layout.set_width(-1)
        if self.grid_stride and self.max_value:
            # if grid stride is less than 1 then we consider it to be percentage
            if self.grid_stride < 1:
                grid_stride = int(self.max_value * self.grid_stride)
            else:
                grid_stride = int(self.grid_stride)

            context.set_line_width(1)
            for i in range(grid_stride, int(self.max_value), grid_stride):
                y = round(max_bar_size * (i / self.max_value)) + 0.5

                if self.show_scale:
                    self.layout.set_text(self.value_format % i)
                    label_w, label_h = self.layout.get_pixel_size()
                    context.move_to(legend_width - label_w - 8,
                                    y - label_h / 2)
                    self.set_color(self.colors.aluminium[4])
                    context.show_layout(self.layout)

                self.set_color(grid_color)
                self.context.move_to(legend_width, y)
                self.context.line_to(self.width, y)


        #stack keys
        if self.show_stack_labels:
            #put series keys
            self.set_color(label_color);

            y = self.graph_height
            label_y = None

            # if labels are at end, then we need show them for the last bar!
            if self.labels_at_end:
                factors = self.bars[-1]
            else:
                factors = self.bars[0]

            if isinstance(factors, Bar):
                factors = [factors]

            self.layout.set_ellipsize(pango.ELLIPSIZE_END)
            self.layout.set_width(self.graph_x * pango.SCALE)
            if self.labels_at_end:
                self.layout.set_alignment(pango.ALIGN_LEFT)
            else:
                self.layout.set_alignment(pango.ALIGN_RIGHT)

            for j in range(len(factors)):
                factor = factors[j].size
                bar_size = factor * max_bar_size

                if round(bar_size) > 0 and self.stack_keys:
                    label = "%s" % self.stack_keys[j]


                    self.layout.set_text(label)
                    label_w, label_h = self.layout.get_pixel_size()

                    y -= bar_size
                    intended_position = round(y + (bar_size - label_h) / 2)

                    if label_y:
                        label_y = min(intended_position, label_y - label_h)
                    else:
                        label_y = intended_position

                    if self.labels_at_end:
                        label_x = self.graph_x + self.graph_width
                        line_x1 = self.graph_x + self.graph_width - 1
                        line_x2 = self.graph_x + self.graph_width - 6
                    else:
                        label_x = -8
                        line_x1 = self.graph_x - 6
                        line_x2 = self.graph_x


                    context.move_to(label_x, label_y)
                    context.show_layout(self.layout)

                    if label_y != intended_position:
                        context.move_to(line_x1, label_y + label_h / 2)
                        context.line_to(line_x2, round(y + bar_size / 2))

        context.stroke()

import gtk
import gobject
import cairo
import copy
import math

# Tango colors
light = [(252, 233, 79), (252, 175, 62),  (233, 185, 110),
         (138, 226, 52), (114, 159, 207), (173, 127, 168), 
         (239, 41,  41), (238, 238, 236), (136, 138, 133)]

medium = [(237, 212, 0),  (245, 121, 0),   (193, 125, 17),
          (115, 210, 22), (52,  101, 164), (117, 80,  123), 
          (204, 0,   0),  (211, 215, 207), (85, 87, 83)]

dark = [(196, 160, 0), (206, 92, 0),    (143, 89, 2),
        (78, 154, 6),  (32, 74, 135),   (92, 53, 102), 
        (164, 0, 0),   (186, 189, 182), (46, 52, 54)]

color_count = len(light)

def set_color(context, color):
    r,g,b = color[0] / 255.0, color[1] / 255.0, color[2] / 255.0
    context.set_source_rgb(r, g, b)
    
    
class SimpleChart(gtk.DrawingArea):
    """Small charting library that enables you to draw simple bar and
    horizontal bar charts. This library is not intended for scientific graphs.
    More like some visual clues to the user.

    Currently chart understands only list of four member lists, in label, value
    fashion. Like:
        data = [
            ["Label1", value1, color(optional), background(optional)],
            ["Label2", value2 color(optional), background(optional)],
            ["Label3", value3 color(optional), background(optional)],
        ]

    Colores disponibles: 
        0: Amarillo
        1: Naranja
        2: Marrón 
        3: Verde
        4: Azul
        5: Lila
        6: Rojo
        7: Gris
        8: Negro

    Author: toms.baugis@gmail.com
    Feel free to contribute - more info at Project Hamster web page:
    http://projecthamster.wordpress.com/

    Example:
        # create new chart object
        chart = Chart(max_bar_width = 40, collapse_whitespace = True) 
    
        eventBox = gtk.EventBox() # charts go into eventboxes, or windows
        place = self.get_widget("totals_by_day") #just some placeholder
    
        eventBox.add(chart);
        place.add(eventBox)

        #Let's imagine that we count how many apples we have gathered, by day
        data = [["Mon", 20], ["Tue", 12], ["Wed", 80],
                ["Thu", 60], ["Fri", 40], ["Sat", 0], ["Sun", 0]]
        self.day_chart.plot(data)

    =======================================================================

    Chart constructor. Optional arguments:
        orient_vertical = [True|False] - Chart orientation.
                                         Defaults to vertical
        max_bar_width = pixels - Maximal width of bar. If not specified,
                                 bars will stretch to fill whole area
        values_on_bars = [True|False] - Should bar values displayed on each bar.
                                        Defaults to False
        collapse_whitespace = [True|False] - If max_bar_width is set, should
                                             we still fill the graph area with
                                             the white stuff and grids and such.
                                             Defaults to false
        stretch_grid = [True|False] - Should the grid be of fixed or flex
                                      size. If set to true, graph will be split
                                      in 4 parts, which will stretch on resize.
                                      Defaults to False.
        animate = [True|False] - Should the bars grow/shrink on redrawing.
                                 Animation happens only if labels and their
                                 order match.
                                 Defaults to True.
        legend_width = pixels - Legend width in pixels. Will keep you graph
                                from floating horizontally

        Then there are some defaults, you can override:
        default_grid_stride - If stretch_grid is set to false, this allows you
                              to choose granularity of grid. Defaults to 50
        animation_frames - in how many steps should the animation be done
        animation_timeout - after how many miliseconds should we draw next frame
    """
    def __init__(self, **args):
        """here is init"""
        gtk.DrawingArea.__init__(self)
        self.connect("expose_event", self._expose)
        self.data, self.prev_data = None, None #start off with an empty hand
        
        """now see what we have in args!"""
        self.orient_vertical = ("orient" not in args 
                            or args["orient"] == "vertical") # defaults to true
        self.max_bar_width = None
        if "max_bar_width" in args: self.max_bar_width = args["max_bar_width"]
        self.values_on_bars = ("values_on_bars" in args 
                            and args["values_on_bars"]) #defaults to false
        self.collapse_whitespace = ("collapse_whitespace" in args 
                            and args["collapse_whitespace"]) #defaults to false
        self.stretch_grid = "stretch_grid" in args and args["stretch_grid"] #defaults to false
        self.animate = ("animate" not in args 
                            or args["animate"]) # defaults to true
        self.legend_width = None
        if "legend_width" in args: 
            self.legend_width = args["legend_width"]
        #and some defaults
        self.default_grid_stride = 50
        self.animation_frames = 150
        self.animation_timeout = 20 #in miliseconds
        self.current_frame = self.animation_frames
        self.freeze_animation = False
        
    def _expose(self, widget, event): # expose is when drawing's going on
        context = widget.window.cairo_create()
        context.rectangle(event.area.x, 
                          event.area.y, 
                          event.area.width, 
                          event.area.height)
        context.clip()
        if self.orient_vertical:
            # for simple bars figure, when there is way too much data for bars
            # and go to lines (yay!)
            if (len(self.data) == 0 
                or (widget.allocation.width 
                    / len(self.data)) > 30): #this is big enough
                self._bar_chart(context)
            else:
                self._area_chart(context)
        else:
            self._horizontal_bar_chart(context)
        return False

    def plot(self, data):
        """Draw chart with given data
            Currently chart understands only list of two member lists, 
            in label, value fashion. Like:
                data = [
                    ["Label1", value1],
                    ["Label2", value2],
                    ["Label3", value3],
                ]
        """
        #check if maybe this chart is animation enabled and we are in 
        # middle of animation
        if self.animate and self.current_frame < self.animation_frames: 
            #something's going on here!
            self.freeze_animation = True    # so we don't catch some nasty 
                                            # race condition
            
            self.prev_data = copy.copy(self.data)
            self.new_data, self.max = self._get_factors(data)
            
            #if so, let's start where we are and move to the new set inst
            self.current_frame = 0 #start the animation from beginning
            self.freeze_animation = False
            return
        if self.animate:
            """chart animation means gradually moving from previous data set
               to the new one. prev_data will be the previous set, new_data
               is copy of the data we have been asked to plot, and data itself
               will be the moving thing"""
            self.current_frame = 0
            self.new_data, self.max = self._get_factors(data)
            if not self.prev_data:  # if there is no previous data, set it to 
                                    # zero, so we get a growing animation
                self.prev_data = copy.deepcopy(self.new_data)
                for i in range(len(self.prev_data)):
                    self.prev_data[i]["factor"] = 0
            self.data = copy.copy(self.prev_data)
            gobject.timeout_add(self.animation_timeout, self._replot)
        else:
            self.data, self.max = self._get_factors(data)
            self._invalidate()

    def _replot(self):
        """Internal function to do the math, going from previous set to the
           new one, and redraw graph"""
        if self.freeze_animation:
            return True #just wait until they release us!

        if self.window:    #this can get called before expose    
            # do some sanity checks before thinking about animation
            # are the source and target of same length?
            if len(self.prev_data) != len(self.new_data):
                self.prev_data = copy.copy(self.new_data)
                self.data = copy.copy(self.new_data)
                self.current_frame = self.animation_frames #stop animation
                self._invalidate()
                return False
            
            # have they same labels? (that's important!)
            for i in range(len(self.prev_data)):
                if self.prev_data[i]["label"] != self.new_data[i]["label"]:
                    self.prev_data = copy.copy(self.new_data)
                    self.data = copy.copy(self.new_data)
                    self.current_frame = self.animation_frames #stop animation
                    self._invalidate()
                    return False

            #ok, now we are good!
            self.current_frame = self.current_frame + 1

            # using sines for some "swoosh" animation (not really noticeable)
            # sin(0) = 0; sin(pi/2) = 1
            pi_factor = math.sin((math.pi / 2.0) 
                * (self.current_frame / float(self.animation_frames)))
            #pi_factor = math.sqrt(pi_factor) #stretch it a little so the 
                # animation can be seen a little better
            
            # here we do the magic - go from prev to new
            # we are fiddling with the calculated sizes instead of raw 
            # data - that's much safer
            bars_below_lim = 0
            
            for i in range(len(self.data)):
                diff_in_factors = (self.prev_data[i]["factor"] 
                    - self.new_data[i]["factor"])
                diff_in_values = (self.prev_data[i]["value"] 
                    - self.new_data[i]["value"])
                
                if abs(diff_in_factors * pi_factor) < 0.001:
                    bars_below_lim += 1
                
                self.data[i]["factor"] = (self.prev_data[i]["factor"] 
                    - (diff_in_factors * pi_factor))
                self.data[i]["value"] = (self.prev_data[i]["value"] 
                    - (diff_in_values * pi_factor))
                
            if bars_below_lim == len(self.data): 
                #all bars done - stop animation!
                self.current_frame = self.animation_frames

        if self.current_frame < self.animation_frames:
            self._invalidate()
            return True
        else:
            self.data = copy.copy(self.new_data)
            self.prev_data = copy.copy(self.new_data)
            self._invalidate()
            return False

    def _invalidate(self):
        """Force redrawal of chart"""
        if self.window:    # this can get called before expose 
            alloc = self.get_allocation()
            rect = gtk.gdk.Rectangle(alloc.x, 
                                     alloc.y, 
                                     alloc.width, 
                                     alloc.height)
            self.window.invalidate_rect(rect, True)
            self.window.process_updates(True)
    
    def _get_factors(self, data):
        """get's max value out of data and calculates each record's factor
           against it"""
        max_value = 0
        self.there_are_floats = False
        self.there_are_colors = False
        self.there_are_backgrounds = False
        
        for i in range(len(data)):
            max_value = max(max_value, data[i][1])
            if isinstance(data[i][1], float):
                self.there_are_floats = True    # we need to know for 
                                                # the scale labels
                
            if len(data[i]) > 3 and data[i][2] != None:
                self.there_are_colors = True
                
            if len(data[i]) > 4 and data[i][3] != None:
                self.there_are_backgrounds = True
        
        res = []
        for i in range(len(data)):
            # Sintaxis no válida en python 2.4
            # factor = data[i][1] / float(max_value) if max_value > 0 else 0
            if max_value > 0:
                factor = data[i][1] / float(max_value)
            else:
                factor = 0
            
            if len(data[i]) > 2:
                color = data[i][2]
            else: 
                color = None
            if len(data[i]) > 3:
                background = data[i][3] 
            else:
                background = None
            res.append({"label": data[i][0],
                        "value": data[i][1],
                        # Sintaxis no válida en python 2.4
                        # "color": data[i][2] if len(data[i]) > 2 else None,
                        "color": color,
                        # Sintaxis no válida en python < 2.5
                        #"background": data[i][3] if len(data[i]) > 3 else None,
                        "background": background,
                        "factor": factor
                        })
        
        return res, max_value

    def _draw_bar(self, context, x, y, w, h, color):
        """ draws a nice bar"""
        context.rectangle(x, y, w, h)
        set_color(context, dark[color])
        context.fill_preserve()    
        context.stroke()

        if w > 2 and h > 2:
            context.rectangle(x + 1, y + 1, w - 2, h - 2)
            set_color(context, light[color])
            context.fill_preserve()    
            context.stroke()

        if w > 3 and h > 3:
            context.rectangle(x + 2, y + 2, w - 4, h - 4)
            set_color(context, medium[color])
            context.fill_preserve()    
            context.stroke()
    
    def _bar_chart(self, context):
        rect = self.get_allocation()  #x, y, width, height 
        data, records = self.data, len(self.data)

        if not data:
            return

        # graph box dimensions
        graph_x = self.legend_width or 50 #give some space to scale labels
        graph_width = rect.width + rect.x - graph_x
        
        step = graph_width / float(records)
        if self.max_bar_width:
            step = min(step, self.max_bar_width)
            if self.collapse_whitespace:
                graph_width = step * records #no need to have that white stuff

        graph_y = rect.y
        graph_height = graph_y - rect.x + rect.height - 15
        
        max_size = graph_height - 15

        context.set_line_width(1)
        
        # TODO put this somewhere else - drawing background and some grid
        context.rectangle(graph_x - 1, graph_y, graph_width, graph_height)
        context.set_source_rgb(1, 1, 1)
        context.fill_preserve()
        context.stroke()

        #backgrounds
        if self.there_are_backgrounds:
            for i in range(records):
                if data[i]["background"] != None:
                    set_color(context, light[data[i]["background"]]);
                    context.rectangle(graph_x + (step * i), 
                                      0, 
                                      step, 
                                      graph_height)
                    context.fill_preserve()
                    context.stroke()

        context.set_line_width(1)
        context.set_dash ([1, 3]);
        set_color(context, dark[8])
        
        # scale lines
        # Sintaxis no válida para python < 2.5
        # stride = self.default_grid_stride if self.stretch_grid == False else int(graph_height / 4)
        if self.stretch_grid == False:
            stride = self.default_grid_stride
        else: 
            stride = int(graph_height / 4)
            
        for y in range(graph_y, graph_y + graph_height, stride):
            context.move_to(graph_x - 10, y)
            context.line_to(graph_x + graph_width, y)

        # and borders on both sides, so the graph doesn't fall out
        context.move_to(graph_x - 1, graph_y)
        context.line_to(graph_x - 1, graph_y + graph_height + 1)
        context.move_to(graph_x + graph_width, graph_y)
        context.line_to(graph_x + graph_width, graph_y + graph_height + 1)
        

        context.stroke()
        
        
        context.set_dash ([]);


        # labels
        set_color(context, dark[8]);
        for i in range(records):
            extent = context.text_extents(data[i]["label"]) #x, y, width, height
            context.move_to(graph_x + (step * i) + (step - extent[2]) / 2.0,
                            graph_y + graph_height + 13)
            context.show_text(data[i]["label"])

        # values for max min and average
        # Sintaxis no válida para python <= 2.4
        # max_label = "%.1f" % self.max if self.there_are_floats else "%d" % self.max
        if self.there_are_floats:
            max_label = "%.1f" % self.max 
        else:
            max_label = "%d" % self.max
        extent = context.text_extents(max_label) #x, y, width, height

        context.move_to(graph_x - extent[2] - 16, rect.y + 10)
        context.show_text(max_label)


        #flip the matrix vertically, so we do not have to think upside-down
        context.transform(cairo.Matrix(yy = -1, y0 = graph_height))

        context.set_dash ([]);
        context.set_line_width(0)
        context.set_antialias(cairo.ANTIALIAS_NONE)

        # bars themselves
        for i in range(records):
            # Sintaxis no válida para python <= 2.4
            # color = data[i]["color"] if  data[i]["color"] != None else 3
            if data[i]["color"] != None :
                color = data[i]["color"]
            else:
                color = 3
            bar_size = graph_height * data[i]["factor"]
            #on animations we keep labels on top, so we need some extra space 
            # there
            # Sintaxis no válida para python < 2.5
            #bar_size = bar_size * 0.8 if self.values_on_bars and self.animate else bar_size * 0.9
            if self.values_on_bars and self.animate:
                bar_size = bar_size * 0.8 
            else: 
                bar_size *= 0.9
            bar_size = max(bar_size, 1)
            
            gap = step * 0.05
            bar_x = graph_x + (step * i) + gap
            bar_width = step - (gap * 2)
            
            self._draw_bar(context, bar_x, 0, bar_width, bar_size, color)



        #values
        #flip the matrix back, so text doesn't come upside down
        context.transform(cairo.Matrix(yy = -1, y0 = 0))
        set_color(context, dark[8])        
        context.set_antialias(cairo.ANTIALIAS_DEFAULT)

        if self.values_on_bars:
            for i in range(records):
                # Esta sintaxis necesita Python >= 2.5
                # label = "%.1f" % data[i]["value"] if self.there_are_floats else "%d" % data[i]["value"]
                if self.there_are_floats:
                    label = "%.1f" % data[i]["value"] 
                else:
                    label = "%d" % data[i]["value"]
                extent = context.text_extents(label) #x, y, width, height
                
                bar_size = graph_height * data[i]["factor"]
                
                # bar_size = bar_size * 0.8 if self.animate else bar_size * 0.9
                if self.animate:
                    bar_size = bar_size * 0.8 
                else:
                    bar_size = bar_size * 0.9
                    
                vertical_offset = (step - extent[2]) / 2.0
                
                if self.animate or bar_size - vertical_offset < extent[3]:
                    graph_y = -bar_size - 3
                else:
                    graph_y = -bar_size + extent[3] + vertical_offset
                
                context.move_to(graph_x + (step * i) + (step - extent[2]) / 2.0,
                                graph_y)
                context.show_text(label)


    def _ellipsize_text (self, context, text, width):
        """try to constrain text into pixels by ellipsizing end
           TODO - check if cairo maybe has ability to ellipsize automatically
        """
        extent = context.text_extents(text) #x, y, width, height
        if extent[2] <= width:
            return text
        
        res = text
        while res:
            res = res[:-1]
            extent = context.text_extents(res + "…") #x, y, width, height
            if extent[2] <= width:
                return res + "…"
        
        return text # if can't fit - return what we have
        
    def _horizontal_bar_chart(self, context):
        rect = self.get_allocation()  #x, y, width, height
        data, records = self.data, len(self.data)
        
        # ok, start with labels - get the longest now
        # TODO - figure how to wrap text
        if self.legend_width:
            max_extent = self.legend_width
        else:
            max_extent = 0
            for i in range(records):
                extent = context.text_extents(data[i]["label"]) #x, y, width, height
                max_extent = max(max_extent, extent[2] + 8)
        
        
        #push graph to the right, so it doesn't overlap, and add little padding aswell
        graph_x = rect.x + max_extent
        graph_width = rect.width + rect.x - graph_x

        graph_y = rect.y
        graph_height = graph_y - rect.x + rect.height
        
        if records > 0: 
            step = int(graph_height / float(records))
        else:
            step = 30
        if self.max_bar_width:
            step = min(step, self.max_bar_width)
            if self.collapse_whitespace:
                graph_height = step * records #resize graph accordingly
        
        max_size = graph_width - 15


        ellipsize_label = lambda(text): 3

        #now let's put the labels and align them right
        set_color(context, dark[8]);
        for i in range(records):
            label = data[i]["label"]
            if self.legend_width:
                label = self._ellipsize_text(context, label, max_extent - 8)
            extent = context.text_extents(label) #x, y, width, height
            
            context.move_to(rect.x + max_extent - extent[2] - 8, rect.y + (step * i) + (step + extent[3]) / 2)
            context.show_text(label)
        
        context.stroke()        
        
        
        context.set_line_width(1)
        
        # TODO put this somewhere else - drawing background and some grid
        context.rectangle(graph_x, graph_y, graph_width, graph_height)
        context.set_source_rgb(1, 1, 1)
        context.fill_preserve()
        context.stroke()


        context.set_dash ([1, 3]);
        set_color(context, dark[8])

        # scale lines        
        #grid_stride = self.default_grid_stride if self.stretch_grid == False else (graph_width) / 3.0
        if not self.stretch_grid: 
            grid_stride = self.default_grid_stride
        else:
            grid_stride = (graph_width) / 3.0
        for x in range(int(graph_x + grid_stride), 
                       int(graph_x + graph_width - grid_stride), 
                       int(grid_stride)):
            context.move_to(x, graph_y)
            context.line_to(x, graph_y + graph_height)

        context.move_to(graph_x + graph_width, graph_y)
        context.line_to(graph_x + graph_width, graph_y + graph_height)


        # and borders on both sides, so the graph doesn't fall out
        context.move_to(graph_x, graph_y)
        context.line_to(graph_x + graph_width, graph_y)
        context.move_to(graph_x, graph_y + graph_height)
        context.line_to(graph_x + graph_width, graph_y + graph_height)

        context.stroke()

        gap = step * 0.05
        
        context.set_dash ([]);
        context.set_line_width(0)
        context.set_antialias(cairo.ANTIALIAS_NONE)

        # bars themselves
        for i in range(records):
            #color = data[i]["color"] if  data[i]["color"] != None else 3
            if data[i]["color"] != None:
                color = data[i]["color"]
            else:
                color = 3
            bar_y = graph_y + (step * i) + gap
            bar_size = max_size * data[i]["factor"]
            bar_size = max(bar_size, 1)
            bar_height = step - (gap * 2)

            self._draw_bar(context, graph_x, bar_y, bar_size, bar_height, color)


        #values
        context.set_antialias(cairo.ANTIALIAS_DEFAULT)
        set_color(context, dark[8])        
        if self.values_on_bars:
            for i in range(records):
                #label = "%.1f" % data[i]["value"] if self.there_are_floats else "%d" % data[i]["value"]
                if self.there_are_floats:
                    label = "%.1f" % data[i]["value"]
                else:
                    label = "%d" % data[i]["value"]
                extent = context.text_extents(label) #x, y, width, height
                
                bar_size = max_size * data[i]["factor"]
                horizontal_offset = (step + extent[3]) / 2.0 - extent[3]
                
                if  bar_size - horizontal_offset < extent[2]:
                    label_x = graph_x + bar_size + horizontal_offset
                else:
                    label_x = graph_x + bar_size - extent[2] - horizontal_offset
                
                context.move_to(label_x, graph_y + (step * i) + (step + extent[3]) / 2.0)
                context.show_text(label)

        else:
            # values for max min and average
            context.move_to(graph_x + graph_width + 10, graph_y + 10)
            #max_label = "%.1f" % self.max if self.there_are_floats else "%d" % self.max
            if self.there_are_floats:
                max_label = "%.1f" % self.max 
            else: 
                max_label = "%d" % self.max
            context.show_text(max_label)
        
        
    def _area_chart(self, context):
        rect = self.get_allocation()  #x, y, width, height        
        data, records = self.data, len(self.data)

        if not data:
            return

        # graph box dimensions
        graph_x = self.legend_width or 50 #give some space to scale labels
        graph_width = rect.width + rect.x - graph_x
        
        step = graph_width / float(records)
        graph_y = rect.y
        graph_height = graph_y - rect.x + rect.height - 15
        
        max_size = graph_height - 15



        context.set_line_width(1)
        
        # TODO put this somewhere else - drawing background and some grid
        context.rectangle(graph_x, graph_y, graph_width, graph_height)
        context.set_source_rgb(1, 1, 1)
        context.fill_preserve()
        context.stroke()

        context.set_line_width(1)
        context.set_dash ([1, 3]);


        #backgrounds
        if self.there_are_backgrounds:
            for i in range(records):
                if data[i]["background"] != None:
                    set_color(context, light[data[i]["background"]]);
                    context.rectangle(graph_x + (step * i), 1, step, graph_height - 1)
                    context.fill_preserve()
                    context.stroke()

            
        set_color(context, dark[8])
        
        # scale lines
        #stride = self.default_grid_stride if self.stretch_grid == False else int(graph_height / 4)
        if not self.stretch_grid:
            stride = self.default_grid_stride
        else:
            stride = int(graph_height / 4)
            
        for y in range(graph_y, graph_y + graph_height, stride):
            context.move_to(graph_x - 10, y)
            context.line_to(graph_x + graph_width, y)

        # and borders on both sides, so the graph doesn't fall out
        context.move_to(graph_x - 1, graph_y)
        context.line_to(graph_x - 1, graph_y + graph_height + 1)
        context.move_to(graph_x + graph_width, graph_y)
        context.line_to(graph_x + graph_width, graph_y + graph_height + 1)
        

        context.stroke()
        
        
        context.set_dash ([]);

        # labels
        set_color(context, dark[8]);
        for i in range(records):
            if i % 5 == 0:
                context.move_to(graph_x + 5 + (step * i), graph_y + graph_height + 13)
                context.show_text(data[i]["label"])

        # values for max min and average
        #max_label = "%.1f" % self.max if self.there_are_floats else "%d" % self.max
        if self.there_are_floats:
            max_label = "%.1f" % self.max 
        else:
            max_label = "%d" % self.max
        extent = context.text_extents(max_label) #x, y, width, height

        context.move_to(graph_x - extent[2] - 16, rect.y + 10)
        context.show_text(max_label)


        context.rectangle(graph_x, graph_y, graph_width, graph_height + 1)
        context.clip()

        #flip the matrix vertically, so we do not have to think upside-down
        context.transform(cairo.Matrix(yy = -1, y0 = graph_height))


        set_color(context, dark[4]);
        # chart itself
        for i in range(records):
            if i == 0:
                context.move_to(graph_x, -10)
                context.line_to(graph_x, graph_height * data[i]["factor"] * 0.9)
                
            context.line_to(graph_x + (step * i) + (step * 0.5), graph_height * data[i]["factor"] * 0.9)

            if i == records - 1:
                context.line_to(graph_x  + (step * i) + (step * 0.5),  0)
                context.line_to(graph_x + graph_width, 0)
                context.line_to(graph_x + graph_width, -10)
                


        set_color(context, light[4])
        context.fill_preserve()    

        context.set_line_width(3)
        context.set_line_join (cairo.LINE_JOIN_ROUND);
        set_color(context, dark[4]);
        context.stroke()    
        

# Funciones para ser un poquito más feliz: se le pasa el contenedor, las 
# claves y los valores (opcionalmente algún que otro parámetro más) y listo.

def add_grafica_barras_horizontales(contenedor, claves, valores):
    alignment = gtk.Alignment(0.5, 0.5, 0.9, 0.9)
    grafica = Chart(value_format = "%.1f",
                    max_bar_width = 20,
                    legend_width = 70,
                    interactive = False)
    grafica.plot(claves, valores)
    alignment.add(grafica)
    contenedor.add(alignment)
    contenedor.show_all()
    return grafica
        
def add_grafica_barras_verticales(contenedor, claves, valores, montones = [""], 
                                  colores = {"": None}, 
                                  ver_botones_colores = True, 
                                  ver_etiquetas_montones = None):
    if valores and not isinstance(valores[0], (list, tuple)):
        # Necesito una lista de listas de enteros. Cada "sublista" se 
        # corresponde con una clave. Lo que me la llegado es una única 
        # lista con esos valores.
        valores = [[i] for i in valores]
    if ver_etiquetas_montones is None:
        ver_etiquetas_montones = len(montones) > 1
    if len(colores.keys()) < len(montones):
        colores = dict([(stack, None) for stack in montones])
    grafica = BarChart(background = "#fafafa",
                       bar_base_color = (220, 220, 220),
                       legend_width = 70,
                       show_stack_labels = ver_etiquetas_montones, 
                       values_on_bars = True)
    if ver_botones_colores:
        def on_color_set(button, montones, stack_idx, grafica, colores):
            colores[stack_idx] = button.get_color().to_string()
            grafica.stack_key_colors = colores
            grafica.plot(claves, valores, montones)
        box = gtk.HBox()
        box.pack_start(grafica)
        color_buttons = gtk.VBox()
        color_buttons.set_spacing(4)
        i = 0
        for stack in montones:
            color = [rgb * 255.0/65535 for rgb in grafica.get_bar_color(i)]
            button = gtk.ColorButton(gtk.gdk.Color(*color))
            button.connect("color-set", 
                           on_color_set, montones, stack, grafica, colores)
            color_buttons.pack_start(gtk.Label(stack), expand = False)
            color_buttons.pack_start(button)
            i += 1
        box.pack_start(color_buttons, False)
    alignment = gtk.Alignment(0.5, 0.5, 0.9, 0.9)
    if ver_botones_colores:
        alignment.add(box)
    else:
        alignment.add(grafica)
    contenedor.add(alignment)
    contenedor.show_all()
    grafica.stack_key_colors = colores
    grafica.plot(claves, valores, montones)
    return grafica

def add_grafica_rangos(contenedor, claves, valores):
    alignment = gtk.Alignment(0.5, 0.5, 0.9, 0.9)
    grafica = HorizontalDayChart(80, 70)        
    grafica.plot_day(claves, valores)
    alignment.add(grafica)
    contenedor.add(alignment)
    contenedor.show_all()
    return grafica

def add_grafica_simple(contenedor, claves, valores):
    e = gtk.EventBox()
    c = SimpleChart()
    e.add(c)
    data = zip(claves, valores)
    c.plot(data)
    contenedor.add(e)
    contenedor.show_all()
    return c
