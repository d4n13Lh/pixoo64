"""
Pixel Display - Divoom Pixoo64 Display Controller

This module provides functionality to control a Divoom Pixoo64 display device,
including drawing primitives, animations, and device control commands.
"""

from typing import List, Optional, Tuple

import aiohttp
import base64

from PIL import Image, ImageSequence


class Pixoo64Animation:
    """
    Represents an animated GIF for the Pixoo64 device.
    
    Contains properties that remain constant across all commands.
    """
    
    def __init__(self, encoded_frames: List[bytes], frame_delay: int, pic_width: int):
        """
        Initialize the animated image.
        
        Args:
            encoded_frames: List of encoded frame data
            frame_delay: Delay between frames in milliseconds
            pic_width: Width of the image
        """
        self.encoded_frames = encoded_frames
        self.frame_delay = frame_delay
        self.pic_width = pic_width

    @classmethod
    def load_from_gif(cls, gif_path: str, pic_width: int = 64) -> 'Pixoo64Animation':
        """
        Load encoded frames and frame delay from a GIF file.
        
        Args:
            gif_path: Path to the GIF file
            pic_width: Width to resize the image to (default: 64)
            
        Returns:
            Pixoo64Animation instance
        """
        with Image.open(gif_path) as img:
            encoded_frames = []
            for frame in ImageSequence.Iterator(img):
                # Scale frame to pic_width x pic_width pixels
                frame = frame.resize((pic_width, pic_width), Image.Resampling.LANCZOS)
                # Convert frame to RGB format and then to bytes
                frame_rgb = frame.convert('RGB')
                frame_data = frame_rgb.tobytes()
                print(f"Frame data length: {len(frame_data)}")
                encoded_frames.append(frame_data)
            frame_delay = img.info.get('duration', 100)  # Default to 100 ms if not specified
        return cls(encoded_frames, frame_delay, pic_width)


class DivoomPixoo64:
    """Divoom Pixoo64 display controller with drawing capabilities."""
    
    def __init__(self, ip_address: str, port: int = 80, initial_pic_id: int = 0):
        """
        Initialize the Divoom Pixoo64 client.
        
        Args:
            ip_address: IP address of the device
            port: Port number (default: 80)
        """
        self.ip_address = ip_address
        self.base_url = f"http://{ip_address}:{port}"
        self.buffer_width = 64
        self._pic_id_counter = initial_pic_id
        self._init_buffer()
        
    def _init_buffer(self) -> None:
        """Initialize the internal frame buffer."""
        self._buffer = Image.new('RGB', (self.buffer_width, self.buffer_width), (0, 0, 0))

    def _get_next_pic_id(self) -> int:
        """Get the next available pic_id."""
        self._pic_id_counter += 1
        return self._pic_id_counter

    def set_pixel(self, x: int, y: int, color: Tuple[int, int, int]) -> None:
        """
        Set an individual pixel in the internal buffer.
        
        Args:
            x: X coordinate (0-63)
            y: Y coordinate (0-63)
            color: (R, G, B) tuple
            
        Raises:
            ValueError: If coordinates are out of bounds
        """
        if 0 <= x < self.buffer_width and 0 <= y < self.buffer_width:
            self._buffer.putpixel((x, y), color)
        else:
            raise ValueError(f"Pixel coordinates out of bounds: ({x}, {y})")

    def clear_buffer(self, color: Tuple[int, int, int] = (0, 0, 0)) -> None:
        """
        Clear the buffer to a single color.
        
        Args:
            color: (R, G, B) tuple (default: black)
        """
        self._buffer.paste(color, (0, 0, self.buffer_width, self.buffer_width))

    async def flush_buffer(self, pic_id: Optional[int] = None, frame_delay: int = 100) -> None:
        """
        Flush the current buffer to the display as a single-frame animation.
        
        Args:
            pic_id: Picture ID to use (auto-incremented if None)
            frame_delay: Frame delay in ms (default: 100)
        """
        if pic_id is None:
            pic_id = self._get_next_pic_id()
        frame_data = self._buffer.tobytes()
        animation = Pixoo64Animation([frame_data], frame_delay, self.buffer_width)
        await self.display_animation(animation, pic_id)

    async def send_command(self, payload: dict) -> dict:
        """
        Send a command to the device.
        
        Args:
            payload: Command payload to send
            
        Returns:
            Response from the device
        """
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/post"
            headers = {'Content-Type': 'application/json'}
            print(f"Sending request to {url}")
            print(f"Payload: {payload}")
            async with session.post(url, json=payload, headers=headers) as response:
                try:
                    response_data = await response.json()
                    print(f"Response: {response_data}")
                    return response_data
                except Exception:
                    # If JSON parsing fails, just return success if status is 200
                    success = {'success': response.status == 200}
                    print(f"Failed to parse JSON response. Status: {response.status}")
                    print(f"Response text: {await response.text()}")
                    return success
                
    async def reboot(self) -> dict:
        """Reboot the Divoom device using Device/SysReboot command."""
        payload = {"Command": "Device/SysReboot"}
        return await self.send_command(payload)

    async def set_brightness(self, brightness: int) -> dict:
        """
        Set display brightness.
        
        Args:
            brightness: Brightness level (0-100)
        """
        payload = {
            "Command": "Channel/SetBrightness",
            "Brightness": brightness
        }
        return await self.send_command(payload)

    async def display_animation(self, image: Pixoo64Animation, pic_id: Optional[int] = None) -> None:
        """
        Display an animated image on the device.
        
        Executes Draw/SendHttpGif command in a loop for each frame.
        
        Args:
            image: Pixoo64Animation to display
            pic_id: Picture ID to use (auto-incremented if None)
            
        Raises:
            ValueError: If no frames to display
        """
        if not image.encoded_frames:
            raise ValueError("No frames to display")
        
        if pic_id is None:
            pic_id = self._get_next_pic_id()
        
        pic_num = min(len(image.encoded_frames), 60)
        pic_width = image.pic_width
        for pic_offset, frame in enumerate(image.encoded_frames[:60]):
            print(f"{len(frame)}")
            payload = {
                "Command": "Draw/SendHttpGif",
                "PicNum": pic_num,
                "PicWidth": pic_width,
                "PicOffset": pic_offset,
                "PicID": pic_id,
                "PicSpeed": image.frame_delay,
                "PicData": base64.b64encode(frame).decode('utf-8')
            }
            await self.send_command(payload)

    async def display_text(self, text: str) -> dict:
        """
        Display text on the device according to Divoom API spec.
        
        Args:
            text: Text to display
        """
        payload = {
            "Command": "Draw/SendHttpText",
            "TextId": 1,
            "align": 1,
            "x": 0,
            "y": 40,
            "dir": 0,
            "font": 1,
            "TextWidth": 40,
            "speed": 10,
            "TextString": text,
            "color": "#FFFFFF"
        }
        return await self.send_command(payload)

    async def set_scoreboard(self, blue_score: int, red_score: int) -> dict:
        """
        Set the scores on the scoreboard display.
        
        Args:
            blue_score: Score for the blue team
            red_score: Score for the red team
        """
        payload = {
            "Command": "Tools/SetScoreBoard",
            "BlueScore": blue_score,
            "RedScore": red_score
        }
        return await self.send_command(payload)

    async def play_buzzer(self, active_time: int = 500, off_time: int = 500, 
                         total_time: int = 3000) -> dict:
        """
        Play the device's buzzer with specified timing parameters.
        
        Args:
            active_time: Duration in ms that the buzzer is active in each cycle
            off_time: Duration in ms that the buzzer is off in each cycle
            total_time: Total duration in ms to play the buzzer
        """
        payload = {
            "Command": "Device/PlayBuzzer",
            "ActiveTimeInCycle": active_time,
            "OffTimeInCycle": off_time,
            "PlayTotalTime": total_time
        }
        return await self.send_command(payload)

    async def set_timer(self, minutes: int = 0, seconds: int = 0, 
                       status: int = 1) -> dict:
        """
        Set and control the device's timer.
        
        Args:
            minutes: Number of minutes for the timer
            seconds: Number of seconds for the timer
            status: Timer status - 1 to start/set, 0 to stop
        """
        payload = {
            "Command": "Tools/SetTimer",
            "Minute": minutes,
            "Second": seconds,
            "Status": status
        }
        return await self.send_command(payload)

    def draw_line(self, x0: int, y0: int, x1: int, y1: int, 
                  color: Tuple[int, int, int]) -> None:
        """
        Draw a line from (x0, y0) to (x1, y1) using set_pixel.
        
        Args:
            x0: Start X coordinate
            y0: Start Y coordinate
            x1: End X coordinate
            y1: End Y coordinate
            color: (R, G, B) tuple
        """
        # Bresenham's line algorithm
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        if dx > dy:
            err = dx // 2
            while x != x1:
                self.set_pixel(x, y, color)
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
            self.set_pixel(x, y, color)  # Set last pixel
        else:
            err = dy // 2
            while y != y1:
                self.set_pixel(x, y, color)
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy
            self.set_pixel(x, y, color)  # Set last pixel

    def draw_circle(self, cx: int, cy: int, radius: int, 
                   outline_color: Tuple[int, int, int], 
                   fill_color: Optional[Tuple[int, int, int]] = None) -> None:
        """
        Draw a circle at (cx, cy) with the given radius.
        
        Args:
            cx: Center X coordinate
            cy: Center Y coordinate
            radius: Radius of the circle
            outline_color: (R, G, B) tuple for the outline
            fill_color: (R, G, B) tuple for the fill (optional)
        """
        # Fill (optional)
        if fill_color is not None:
            for y_off in range(-radius, radius + 1):
                for x_off in range(-radius, radius + 1):
                    if x_off * x_off + y_off * y_off <= radius * radius:
                        px, py = cx + x_off, cy + y_off
                        if 0 <= px < self.buffer_width and 0 <= py < self.buffer_width:
                            self.set_pixel(px, py, fill_color)
        # Midpoint circle algorithm for outline
        x = radius
        y = 0
        d = 1 - radius
        outline_points = set()
        while x >= y:
            outline_points.update([
                (cx + x, cy + y), (cx - x, cy + y), (cx + x, cy - y), (cx - x, cy - y),
                (cx + y, cy + x), (cx - y, cy + x), (cx + y, cy - x), (cx - y, cy - x)
            ])
            y += 1
            if d < 0:
                d += 2 * y + 1
            else:
                x -= 1
                d += 2 * (y - x) + 1
        for px, py in outline_points:
            if 0 <= px < self.buffer_width and 0 <= py < self.buffer_width:
                self.set_pixel(px, py, outline_color)

    def draw_rectangle(self, x0: int, y0: int, x1: int, y1: int,
                      outline_color: Tuple[int, int, int],
                      fill_color: Optional[Tuple[int, int, int]] = None) -> None:
        """
        Draw a rectangle from (x0, y0) to (x1, y1).
        
        Args:
            x0: Top-left X coordinate
            y0: Top-left Y coordinate
            x1: Bottom-right X coordinate
            y1: Bottom-right Y coordinate
            outline_color: (R, G, B) tuple for the outline
            fill_color: (R, G, B) tuple for the fill (optional)
        """
        # Fill (optional)
        if fill_color is not None:
            for y in range(min(y0, y1) + 1, max(y0, y1)):
                for x in range(min(x0, x1) + 1, max(x0, x1)):
                    if 0 <= x < self.buffer_width and 0 <= y < self.buffer_width:
                        self.set_pixel(x, y, fill_color)
        # Outline
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in [min(y0, y1), max(y0, y1)]:
                if 0 <= x < self.buffer_width and 0 <= y < self.buffer_width:
                    self.set_pixel(x, y, outline_color)
        for y in range(min(y0, y1), max(y0, y1) + 1):
            for x in [min(x0, x1), max(x0, x1)]:
                if 0 <= x < self.buffer_width and 0 <= y < self.buffer_width:
                    self.set_pixel(x, y, outline_color)

