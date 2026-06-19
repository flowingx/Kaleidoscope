# Kaleidoscope Studio Vision

## Current Direction

Kaleidoscope is becoming a drawing board where symmetry is a view, not only a brush effect.

The app now has two kinds of objects:

- **Repeating objects**: shapes and brush marks that participate in the kaleidoscope view.
- **Free objects**: note-like shapes placed at one exact position, without being mirrored into every slice.

This makes the app closer to a visual notebook: users can mix symmetric art with ordinary annotations, stickers, markers, and layout elements.

## Selection Model

The selection tool should behave like a familiar canvas editor:

- **Point**: select and edit one shape.
- **Lasso**: draw around multiple shapes, then move, scale, or delete the group.

This keeps precision for single shapes and gives quick spatial editing for groups.

## Shape Library

The first shape library includes:

- triangle
- star
- square
- diamond
- hexagon
- heart

Future additions can include arrows, labels, frames, callouts, icons, and image-like stamps.

## The "Changing View" Idea

The strongest version of the app is not just "draw repeated marks." It is:

> Place marks on a board, then change the viewing lens and watch the artwork reorganize.

Possible next steps:

- Add a **Lens** panel for changing slice count, mirror mode, center point, and rotation as named presets.
- Let users save several view presets and switch between them.
- Add an animated transition between view presets.
- Keep free objects pinned to the board while repeated objects pass through the kaleidoscope lens.
- Eventually support a draggable lens center, so the same drawing changes when the viewer's angle changes.

This preserves the original kaleidoscope soul while allowing the tool to grow toward a notebook-like canvas.
