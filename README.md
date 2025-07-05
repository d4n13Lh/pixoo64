# pixoo64

Python-Library offering proper drawing-primitives for the pixoo64-device.  
Including also a simulator for the pixoo64, offering the same API like the real device.  
Allows easy testing and fast turn-around-times.


Following functions/graphic-primitives are supported by the python-library


* set_pixel(self, x: int, y: int, color: Tuple[int, int, int]) -> None:
* display_animation(self, image: Pixoo64Animation, pic_id: Optional[int] = None) -> None:
* display_text(self, text: str) -> dict:
* draw_line(self, x0: int, y0: int, x1: int, y1: int, 
* draw_circle(self, cx: int, cy: int, radius: int, 
* draw_rectangle(self, x0: int, y0: int, x1: int, y1: int,
 


## Installation

Install all required dependencies via   
```pip install -r requirements.txt```


## Running

### With simulator

First start the simulator, in background

```python simulator.py```

A pygame based simulator accepting the same API like the original pixoo64 will be started and will be listening on port 8079

Uncomment in main.py line 161 and comment out line 162 

Start the main-programm: 

```python main.py```

The pixoo-simulator will show a nice swiss flag

### With real device

Enter IP-adress of your pixoo-device into line 162 in main.py.

Start the main-programm: 

```python main.py```

The pixoo64 device will show a nice swiss flag

