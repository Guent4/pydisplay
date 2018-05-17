# PyDisplay

This library is designed to help display content using PyGame and is
specifically designed to work well on a Raspberry Pi with a Adafruit
PiTFT screen.  However, it should work with any display but some defaults
might need to be altered slightly.

## Dependencies
This runs on Python 3 so make sure you have Python 3 (and `pip3`) installed.

If you are only using the display properties, you must have `pygame` installed.
You can do this by running:
```
pip3 install pygame
```

To have physical button support, make sure you are using a Raspberry Pi and run:
```
sudo apt-get update
sudo apt-get install rpi.gpio
```

## How to install
Using git, clone this repository inside your working directory:
```
git clone https://github.com/Guent4/pydisplay pydisplay
```

## How to use
Then create a file (alternatively, copy `Demo.py` from inside the `pydisplay`
directory) in your working directory and define your custom pages there.
It is important that all of your custom pages must extend the `Pages.Page`
class.  Refer to `Demo.py` for a good starting tutorial on how to use
this library.

To run the demo, run the following:
```
sudo python3 Demo.py
```

If you are not running on the PiTFT, include the two extra flags:
```
sudo python3 Demo.py --not_on_pitft --disable_button
```

## FAQ
**Q**: A `Drawable` isn't displaying on my page! \
**A**: Make sure that you remembered to append the `Drawable` to your
page's `self._drawables` or else the `Drawable` will never get drawn.