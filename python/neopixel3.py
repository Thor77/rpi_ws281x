# Adafruit NeoPixel library port to the rpi_ws281x library.
# Author: Tony DiCola (tony@tonydicola.com), Jeremy Garff (jer@jers.net)
import atexit

import _rpi_ws281x as ws


class Color(object):
    '''
    Convert the provided red, green, blue color to a 24-bit color value.
    Each color component should be a value 0-255 where 0 is the lowest
    intensity and 255 is the highest intensity.
    '''
    def __init__(self, red, green, blue, white=0):
        self.value = (white << 24) | (red << 16) | (green << 8) | blue


class Adafruit_NeoPixel(object):
    def __init__(self, num, pin, freq_hz=800000, dma=5, invert=False,
                 brightness=255, channel=0, strip_type=ws.WS2811_STRIP_RGB):
        '''
        Class to represent a NeoPixel/WS281x LED display.

        :param num: Number of pixels on the display
        :param pin: GPIO pin connected to the display signal line
        :param freq_hz: Frequency of the display signal
        :param dma: DMA channel to use
        :param invert: Signal line should be inverted
        :param channel: PWM channel to use
        :param strip_type: Type of the connected LED display

        :type num: int
        :type pin: int
        :type freq_hz: int
        :type dma: int
        :type invert: bool
        :type channel: int
        :param strip_type: int
        '''
        # Create ws2811_t structure and fill in parameters.
        self._leds = ws.new_ws2811_t()

        # Initialize the channels to zero
        for channum in range(2):
            chan = ws.ws2811_channel_get(self._leds, channum)
            ws.ws2811_channel_t_count_set(chan, 0)
            ws.ws2811_channel_t_gpionum_set(chan, 0)
            ws.ws2811_channel_t_invert_set(chan, 0)
            ws.ws2811_channel_t_brightness_set(chan, 0)

        # Initialize the channel in use
        self._channel = ws.ws2811_channel_get(self._leds, channel)
        ws.ws2811_channel_t_count_set(self._channel, num)
        ws.ws2811_channel_t_gpionum_set(self._channel, pin)
        ws.ws2811_channel_t_invert_set(self._channel, 0 if not invert else 1)
        ws.ws2811_channel_t_brightness_set(self._channel, brightness)
        ws.ws2811_channel_t_strip_type_set(self._channel, strip_type)

        # Initialize the controller
        ws.ws2811_t_freq_set(self._leds, freq_hz)
        ws.ws2811_t_dmanum_set(self._leds, dma)

        # Substitute for __del__, traps an exit condition and cleans up
        atexit.register(self._cleanup)

        # Initialize libary
        resp = ws.ws2811_init(self._leds)
        if resp != ws.WS2811_SUCCESS:
            message = ws.ws2811_get_return_t_str(resp)
            raise RuntimeError(
                'ws2811_init failed with code {0} ({1})'.format(resp, message))

    def __del__(self):
        # Required because Python will complain about memory leaks
        # However there's no guarantee that "ws" will even be set
        # when the __del__ method for this class is reached.
        if ws is not None:
            self._cleanup()

    def __setitem__(self, position, color):
        self.set_color(position, color)

    def __getitem__(self, position):
        return self.get_color(position)

    @property
    def pixel_count(self):
        '''
        Return the number of pixels on the display.
        '''
        return ws.ws2811_channel_t_count_get(self._channel)

    def _cleanup(self):
        # Clean up memory used by the library when not needed anymore.
        if self._leds is not None:
            ws.ws2811_fini(self._leds)
            ws.delete_ws2811_t(self._leds)
            self._leds = None
            self._channel = None
            # ws2811_fini will free the memory used by led_data internally.

    def show(self):
        '''
        Update the display with the data from the LED buffer.
        '''
        resp = ws.ws2811_render(self._leds)
        if resp != ws.WS2811_SUCCESS:
            message = ws.ws2811_get_return_t_str(resp)
            raise RuntimeError(
                'ws2811_render failed with code {0} ({1})'.format(
                    resp, message)
            )

    def set_color(self, position, color):
        '''
        Set LED at position n to the provided 24-bit color value (in RGB order)
        '''
        # Handle if a slice of positions are passed in by setting the
        # appropriate LED data values to the provided values.
        if isinstance(position, slice):
            index = 0
            for n in range(position.indices(self.size)):
                ws.ws2811_led_set(self.channel, n, color[index])
                index += 1
        # Else assume the passed in value is a number to the position.
        else:
            return ws.ws2811_led_set(self.channel, position, color)

    def set_brightness(self, brightness):
        '''
        Scale each LED in the buffer by the provided brightness.  A brightness
        of 0 is the darkest and 255 is the brightest.
        '''
        ws.ws2811_channel_t_brightness_set(self._channel, brightness)

    def get_pixels(self):
        '''
        Return an object which allows access to the LED display data as if
        it were a sequence of 24-bit RGB values.
        '''
        return self._led_data

    def get_color(self, position):
        '''
        Get the 24-bit RGB color value for the LED at position n.
        '''
        # Handle if a slice of positions are passed in by grabbing all the
        # values and returning them in a list.
        if isinstance(position, slice):
            return [
                ws.ws2811_led_get(self.channel, n)
                for n in range(position.indices(self.size))
            ]
        # Else assume the passed in value is a number to the position.
        else:
            return ws.ws2811_led_get(self.channel, position)
