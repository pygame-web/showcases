import asyncio
import math
import struct
import sys

import pygame
import zengl

pygame.init()
pygame.display.set_mode((1024, 1024), flags=pygame.OPENGL | pygame.DOUBLEBUF, vsync=True)

ctx = zengl.context()

def load_texture(name):
    img = pygame.image.load(name)
    pixels = pygame.image.tobytes(img, 'RGBA')
    return ctx.image(img.get_size(), 'rgba8unorm', pixels)

size = pygame.display.get_window_size()
image = ctx.image(size, 'rgba8unorm', texture=False)
depth = ctx.image(size, 'depth24plus', texture=False)

texture = load_texture('forest.jpg')
vertex_buffer = ctx.buffer(open('blob.bin', 'rb').read())
uniform_buffer = ctx.buffer(size=80)

background = ctx.pipeline(
    vertex_shader='''
        #version 300 es
        precision highp float;

        vec2 vertices[3] = vec2[](
            vec2(-1.0, -1.0),
            vec2(3.0, -1.0),
            vec2(-1.0, 3.0)
        );

        out vec2 v_vertex;

        void main() {
            gl_Position = vec4(vertices[gl_VertexID], 0.0, 1.0);
            v_vertex = vertices[gl_VertexID];
        }
    ''',
    fragment_shader='''
        #version 300 es
        precision highp float;
        precision highp sampler2D;

        const float pi = 3.14159265358979323;

        uniform sampler2D Texture;

        layout (std140) uniform Common {
            mat4 camera_matrix;
            vec4 camera_position;
        };

        in vec2 v_vertex;

        layout (location = 0) out vec4 out_color;

        vec3 hash33(vec3 p3) {
            p3 = fract(p3 * vec3(0.1031, 0.1030, 0.0973));
            p3 += dot(p3, p3.yxz + 33.33);
            return fract((p3.xxy + p3.yxx) * p3.zyx);
        }

        void main() {
            mat4 inv_camera_matrix = inverse(camera_matrix);
            vec4 position_temp = inv_camera_matrix * vec4(v_vertex, -1.0, 1.0);
            vec4 target_temp = inv_camera_matrix * vec4(v_vertex, 1.0, 1.0);
            vec3 position = position_temp.xyz / position_temp.w;
            vec3 target = target_temp.xyz / target_temp.w;
            vec3 direction = normalize(target - position);

            vec3 color = vec3(0.0);
            for (int i = 0; i < 8; i++) {
                vec3 ray = normalize(direction + hash33(vec3(gl_FragCoord.xy, float(i))) * 0.1);
                vec2 uv = vec2(atan(ray.y, ray.x) / pi, ray.z) * 0.5 + 0.5;
                color += texture(Texture, uv).rgb;
            }
            out_color = vec4(color / 8.0, 1.0);
        }
    ''',
    layout=[
        {
            'name': 'Common',
            'binding': 0,
        },
        {
            'name': 'Texture',
            'binding': 0,
        },
    ],
    resources=[
        {
            'type': 'uniform_buffer',
            'binding': 0,
            'buffer': uniform_buffer,
        },
        {
            'type': 'sampler',
            'binding': 0,
            'image': texture,
        },
    ],
    framebuffer=[image],
    topology='triangles',
    vertex_count=3,
)

pipeline = ctx.pipeline(
    vertex_shader='''
        #version 300 es
        precision highp float;

        layout (std140) uniform Common {
            mat4 camera_matrix;
            vec4 camera_position;
        };

        layout (location = 0) in vec3 in_vertex;
        layout (location = 1) in vec3 in_normal;

        out vec3 v_vertex;
        out vec3 v_normal;

        void main() {
            gl_Position = camera_matrix * vec4(in_vertex, 1.0);
            v_vertex = in_vertex;
            v_normal = in_normal;
        }
    ''',
    fragment_shader='''
        #version 300 es
        precision highp float;
        precision highp sampler2D;

        const float pi = 3.14159265358979323;

        uniform sampler2D Texture;

        layout (std140) uniform Common {
            mat4 camera_matrix;
            vec4 camera_position;
        };

        in vec3 v_vertex;
        in vec3 v_normal;

        layout (location = 0) out vec4 out_color;

        void main() {
            vec3 view = normalize(v_vertex - camera_position.xyz);
            vec3 ray = reflect(view, normalize(v_normal));
            vec2 uv = vec2(atan(ray.y, ray.x) / pi, ray.z) * 0.5 + 0.5;
            vec3 color = texture(Texture, uv).rgb;
            out_color = vec4(color, 1.0);
        }
    ''',
    layout=[
        {
            'name': 'Common',
            'binding': 0,
        },
        {
            'name': 'Texture',
            'binding': 0,
        },
    ],
    resources=[
        {
            'type': 'uniform_buffer',
            'binding': 0,
            'buffer': uniform_buffer,
        },
        {
            'type': 'sampler',
            'binding': 0,
            'image': texture,
        },
    ],
    framebuffer=[image, depth],
    topology='triangles',
    cull_face='back',
    vertex_buffers=zengl.bind(vertex_buffer, '3f 3f', 0, 1),
    vertex_count=vertex_buffer.size // zengl.calcsize('3f 3f'),
)

async def main():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        now = pygame.time.get_ticks() / 1000.0

        ctx.new_frame()
        image.clear()
        depth.clear()

        eye = math.sin(now * 0.5) * 5.0, math.cos(now * 0.5) * 5.0, 2.5
        camera = zengl.camera(eye, (0.0, 0.0, 0.0), aspect=1.0, fov=45.0)
        uniform_buffer.write(struct.pack('64s3f4x', camera, *eye))

        background.render()
        pipeline.render()
        image.blit()
        ctx.end_frame()

        pygame.display.flip()
        await asyncio.sleep(0)

asyncio.run(main())
