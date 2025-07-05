import asyncio
from pixoo import DivoomPixoo64, Pixoo64Animation

async def test_pixel_buffer(display: DivoomPixoo64) -> None:
    """Test pixel buffer operations."""
    # Set a red pixel at (0,0), green at (1,1), blue at (2,2)
    display.set_pixel(0, 0, (255, 0, 0))
    display.set_pixel(1, 1, (0, 255, 0))
    display.set_pixel(2, 2, (0, 0, 255))
    # Flush buffer to display
    await display.flush_buffer()
    await asyncio.sleep(2)  # Wait to see the result

    # Clear buffer to white
    display.clear_buffer((255, 255, 255))
    await display.flush_buffer()
    await asyncio.sleep(2)  # Wait to see the result

    # Draw a diagonal line in yellow
    for i in range(10):
        display.set_pixel(i, i, (255, 255, 0))
    await display.flush_buffer()
    await asyncio.sleep(2)

async def test_lines(display: DivoomPixoo64) -> None:
    """Test line drawing."""
    # Draw a red horizontal line
    display.clear_buffer((0, 0, 0))
    display.draw_line(0, 10, 63, 10, (255, 0, 0))
    await display.flush_buffer()
    await asyncio.sleep(2)

    # Draw a green vertical line
    display.clear_buffer((0, 0, 0))
    display.draw_line(20, 0, 20, 63, (0, 255, 0))
    await display.flush_buffer()
    await asyncio.sleep(2)

    # Draw a blue diagonal line
    display.clear_buffer((0, 0, 0))
    display.draw_line(0, 0, 63, 63, (0, 0, 255))
    await display.flush_buffer()
    await asyncio.sleep(2)

    # Draw a white anti-diagonal line
    display.clear_buffer((0, 0, 0))
    display.draw_line(63, 0, 0, 63, (255, 255, 255))
    await display.flush_buffer()
    await asyncio.sleep(2)

async def test_circles(display: DivoomPixoo64) -> None:
    """Test circle drawing."""
    # Draw a red circle outline
    display.clear_buffer((0, 0, 0))
    display.draw_circle(32, 32, 20, (255, 0, 0))
    await display.flush_buffer()
    await asyncio.sleep(2)

    # Draw a green filled circle
    display.clear_buffer((0, 0, 0))
    display.draw_circle(32, 32, 15, (0, 255, 0), fill_color=(0, 128, 0))
    await display.flush_buffer()
    await asyncio.sleep(2)

    # Draw a blue circle with yellow fill
    display.clear_buffer((0, 0, 0))
    display.draw_circle(32, 32, 10, (0, 0, 255), fill_color=(255, 255, 0))
    await display.flush_buffer()
    await asyncio.sleep(2)

async def test_rectangles(display: DivoomPixoo64) -> None:
    """Test rectangle drawing."""
    # Draw a red rectangle outline
    display.clear_buffer((0, 0, 0))
    display.draw_rectangle(10, 10, 54, 54, (255, 0, 0))
    await display.flush_buffer()
    await asyncio.sleep(2)

    # Draw a green filled rectangle
    display.clear_buffer((0, 0, 0))
    display.draw_rectangle(16, 16, 48, 48, (0, 255, 0), fill_color=(0, 128, 0))
    await display.flush_buffer()
    await asyncio.sleep(2)

    # Draw a blue rectangle with yellow fill
    display.clear_buffer((0, 0, 0))
    display.draw_rectangle(20, 20, 44, 44, (0, 0, 255), fill_color=(255, 255, 0))
    await display.flush_buffer()
    await asyncio.sleep(2)

async def test_windows_flag(display: DivoomPixoo64) -> None:
    """Test Windows flag drawing."""
    display.clear_buffer((0, 0, 0))
    # Blue (top left)
    display.draw_rectangle(12, 12, 30, 28, (0, 0, 255), fill_color=(0, 0, 255))
    # Green (bottom left)
    display.draw_rectangle(12, 34, 30, 50, (0, 255, 0), fill_color=(0, 255, 0))
    # Red (top right)
    display.draw_rectangle(34, 12, 52, 28, (255, 0, 0), fill_color=(255, 0, 0))
    # Yellow (bottom right)
    display.draw_rectangle(34, 34, 52, 50, (255, 255, 0), fill_color=(255, 255, 0))
    # White wavy lines (simulate flag wave)
    display.draw_line(12, 22, 52, 18, (255, 255, 255))
    display.draw_line(12, 40, 52, 36, (255, 255, 255))
    await display.flush_buffer()
    await asyncio.sleep(3)

async def test_swiss_flag(display: DivoomPixoo64) -> None:
    """Test Swiss flag drawing."""
    display.clear_buffer((255, 0, 0))  # Red background
    
    # Swiss flag cross: arms are 1/6 of flag width, centered
    # For 64x64: cross arm width = 64/6 ≈ 11 pixels
    cross_width = 11
    center_x, center_y = 32, 32
    
    # Calculate cross dimensions (centered, not extending to edges)
    h_start = center_x - cross_width // 2  # 32 - 5 = 27
    h_end = center_x + cross_width // 2    # 32 + 5 = 37
    
    # Vertical bar (centered, not full height)
    v_length = 40  # Cross arm length
    v_start = center_y - v_length // 2     # 32 - 20 = 12
    v_end = center_y + v_length // 2       # 32 + 20 = 52
    
    # Vertical bar
    display.draw_rectangle(h_start, v_start, h_end, v_end, (255, 255, 255), fill_color=(255, 255, 255))
    # Horizontal bar
    display.draw_rectangle(v_start, h_start, v_end, h_end, (255, 255, 255), fill_color=(255, 255, 255))
    
    await display.flush_buffer()
    await asyncio.sleep(3)

async def run_commands(display: DivoomPixoo64) -> None:
    """Run demonstration commands for the display."""
    # Set brightness to 50%
    await display.set_brightness(50)
    
    # Create an animated image from a GIF file
    #animated_image = Pixoo64Animation.load_from_gif(r'test2.gif', pic_width=64)
    
    # Display animated image
    #await display.display_animation(animated_image)
    #await asyncio.sleep(5)  # Wait to see the result
    
    # Start a 1-minute timer
    #await display.set_timer(minutes=1)

    # Run all tests
    #await test_pixel_buffer(display)
    #await test_lines(display)
    #await test_circles(display)
    #await test_rectangles(display)
    #await test_windows_flag(display)
    await test_swiss_flag(display)


async def main() -> None:
    """Main entry point."""
    # Create display client
    #display = DivoomPixoo64("localhost", port=8079)
    display = DivoomPixoo64("192.168.1.130", port=80, initial_pic_id=401)
    await run_commands(display)


if __name__ == "__main__":
    asyncio.run(main())

