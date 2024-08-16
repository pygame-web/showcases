import asyncio
import sys
import os

import pygame
import zengl

pygame.init()
pygame.display.set_mode((1024, 1024), flags=pygame.OPENGL | pygame.DOUBLEBUF, vsync=True)

ctx = zengl.context()

size = pygame.display.get_window_size()
image = ctx.image(size, 'rgba8unorm')
temp = ctx.image(size, 'rgba8unorm')

pipeline = ctx.pipeline(
    vertex_shader='''
        #version 300 es
        precision highp float;

        vec2 positions[3] = vec2[](
            vec2(-1.0, -1.0),
            vec2(3.0, -1.0),
            vec2(-1.0, 3.0)
        );

        void main() {
            gl_Position = vec4(positions[gl_VertexID], 0.0, 1.0);
        }
    ''',
    fragment_shader='''
        #version 300 es
        precision highp float;

        uniform sampler2D Texture;
        uniform ivec2 Size;

        layout (location = 0) out vec4 out_color;

        int c(int x, int y) {
            ivec2 at = (ivec2(gl_FragCoord.xy) + ivec2(x, y) + Size) % Size;
            return texelFetch(Texture, at, 0).r < 0.5 ? 0 : 1;
        }

        void main() {
            float res;
            int neighbours = c(-1, -1) + c(-1, 0) + c(0, 1) + c(0, -1) + c(-1, 1) + c(1, -1) + c(1, 0) + c(1, 1);
            if (c(0, 0) == 1) {
                res = (neighbours == 2 || neighbours == 3) ? 1.0 : 0.0;
            } else {
                res = (neighbours == 3) ? 1.0 : 0.0;
            }
            out_color = vec4(res, res, res, 1.0);
        }
    ''',
    uniforms={
        'Size': size,
    },
    layout=[
        {
            'name': 'Texture',
            'binding': 0,
        },
    ],
    resources=[
        {
            'type': 'sampler',
            'binding': 0,
            'image': temp,
        },
    ],
    framebuffer=[image],
    topology='triangles',
    vertex_count=3,
)

image.write(os.urandom(size[0] * size[1] * 4))

async def main():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        ctx.new_frame()
        image.blit(temp)
        pipeline.render()
        image.blit()

        mx, my = pygame.mouse.get_pos()
        mx = min(max(int(mx), 0), size[0] - 1)
        my = min(max(size[1] - int(my) - 1, 0), size[1] - 1)
        if pygame.mouse.get_pressed()[0]:
            image.blit(offset=(mx - 100, my - 100), size=(200, 200), crop=(mx - 20, my - 20, 40, 40))

        ctx.end_frame()

        pygame.display.flip()
        await asyncio.sleep(0)

asyncio.run(main())
