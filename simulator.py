"""
Pixoo64 Simulator - Web-based simulator for Divoom Pixoo64 display.

This module provides a web server that simulates the Divoom Pixoo64 device,
allowing testing of display commands without physical hardware.
"""

import asyncio
import json
import base64
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pygame
import time
from aiohttp import web
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AnimationFrame:
    """Represents a single frame in an animation."""
    data: np.ndarray  # Shape: (64, 64, 3)

class AnimationManager:
    """Manages animation frames and playback."""
    
    def __init__(self) -> None:
        """Initialize the animation manager."""
        self.current_animation: List[AnimationFrame] = []
        self.next_animation: List[AnimationFrame] = []
        self.current_frame: int = 0
        self.frame_delay: int = 100
        self.receiving_frames: bool = False
        
    def start_new_animation(self) -> None:
        """Start receiving a new animation sequence."""
        self.receiving_frames = True
        self.next_animation = []
        
    def add_frame(self, frame_data: np.ndarray) -> None:
        """
        Add a new frame to the next_animation buffer.
        
        Args:
            frame_data: Frame data as numpy array
        """
        self.next_animation.append(AnimationFrame(frame_data))
        
    def finalize_animation(self) -> None:
        """Finalize the animation by moving next_animation to current_animation."""
        self.current_frame = 0
        self.current_animation = self.next_animation
        self.receiving_frames = False
        
    def get_current_frame(self) -> Optional[np.ndarray]:
        """
        Get the current frame data, if available.
        
        Returns:
            Current frame data or None if not available
        """
        if not self.current_animation or self.receiving_frames:
            return None
        try:
            return self.current_animation[self.current_frame].data
        except IndexError:
            logger.warning("Frame index out of range, resetting to frame 0")
            self.current_frame = 0
            return None
            
    def advance_frame(self) -> None:
        """Move to the next frame in the animation."""
        if self.current_animation:
            self.current_frame = (self.current_frame + 1) % len(self.current_animation)

class DisplayManager:
    """Manages the pygame display for visualization."""
    
    def __init__(self, scale: int = 8) -> None:
        """
        Initialize the display manager.
        
        Args:
            scale: Scale factor for the display
        """
        self.scale = scale
        self.screen_size = 64 * scale
        pygame.init()
        self.screen = pygame.display.set_mode((self.screen_size, self.screen_size))
        pygame.display.set_caption("Pixoo64 Simulator")
        self.screen.fill((0, 0, 0))
        pygame.display.flip()
        
    def update_display(self, frame: np.ndarray) -> None:
        """
        Update the display with the given frame.
        
        Args:
            frame: Frame data as numpy array
        """
        # Rotate frame 90 degrees clockwise and flip it
        frame = np.rot90(frame, k=-1)
        frame = np.flipud(np.fliplr(frame))
        
        # Convert numpy array to pygame surface
        surface = pygame.Surface((64, 64))
        pygame.surfarray.blit_array(surface, frame)
        
        # Scale up the surface
        scaled = pygame.transform.scale(surface, (self.screen_size, self.screen_size))
        self.screen.blit(scaled, (0, 0))
        pygame.display.flip()
        
    def cleanup(self) -> None:
        """Clean up pygame resources."""
        pygame.quit()

class Pixoo64Simulator:
    """Main simulator class that handles HTTP requests and display management."""
    
    def __init__(self, port: int = 80) -> None:
        """
        Initialize the simulator.
        
        Args:
            port: Port to run the web server on
        """
        self.port = port
        self.running = True
        self.animation_manager = AnimationManager()
        self.display_manager = DisplayManager()
        
    async def handle_post(self, request: web.Request) -> web.Response:
        """
        Handle POST requests to the simulator.
        
        Args:
            request: The incoming HTTP request
            
        Returns:
            HTTP response
        """
        try:
            data: Dict[str, Any] = await request.json()
            command: Optional[str] = data.get('Command')
            logger.info(f"Received command: {command}")
            
            if command == 'Draw/SendHttpGif':
                await self._handle_send_gif(data)
            
            return web.Response(text='{"error_code":0}')
            
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return web.Response(text='{"error_code":1}', status=500)
            
    async def _handle_send_gif(self, data: Dict[str, Any]) -> None:
        """
        Handle the SendHttpGif command.
        
        Args:
            data: Command data containing frame information
        """
        pic_data: Optional[Union[str, bytes]] = data.get('PicData')
        pic_offset: int = data.get('PicOffset', 0)
        pic_num: int = data.get('PicNum', 1)
        self.animation_manager.frame_delay = data.get('PicSpeed', 100)
        
        if pic_data is None:
            logger.error("No PicData provided")
            return
            
        # Decode base64 data and convert to RGB image
        if isinstance(pic_data, str):
            frame_data = base64.b64decode(pic_data)
        else:
            frame_data = pic_data
            
        frame_array = np.frombuffer(frame_data, dtype=np.uint8)
        frame_array = frame_array.reshape((64, 64, 3))
        
        # Start receiving new animation
        if pic_offset == 0:
            self.animation_manager.start_new_animation()
        
        # Add frame
        self.animation_manager.add_frame(frame_array)
        logger.info(f"Received frame {pic_offset + 1}/{pic_num}")
        
        # Finalize if last frame
        if pic_offset == pic_num - 1:
            self.animation_manager.finalize_animation()
            logger.info("Animation update complete")

    async def run_display(self) -> None:
        """Run the display loop."""
        last_frame_time = time.time()
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return

            current_time = time.time()
            if current_time - last_frame_time >= (self.animation_manager.frame_delay / 1000.0):
                frame = self.animation_manager.get_current_frame()
                if frame is not None:
                    self.display_manager.update_display(frame)
                    self.animation_manager.advance_frame()
                last_frame_time = current_time
            
            await asyncio.sleep(1/60)

    async def start(self) -> None:
        """Start the simulator."""
        app = web.Application()
        app.router.add_post('/post', self.handle_post)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', self.port)
        
        await site.start()
        logger.info(f"Simulator running on http://localhost:{self.port}")

        try:
            await self.run_display()
        finally:
            self.running = False
            await runner.cleanup()
            self.display_manager.cleanup()

async def main() -> None:
    """Main entry point for the simulator."""
    simulator = Pixoo64Simulator(port=8079)
    try:
        await simulator.start()
    except KeyboardInterrupt:
        simulator.running = False

if __name__ == "__main__":
    asyncio.run(main()) 