import torch
import os
import cv2
from tqdm import tqdm
from PIL import Image
from io import BytesIO
import numpy as np

from diffusers import ControlNetModel
from diffusers import DPMSolverMultistepScheduler
from diffusers.models import AutoencoderKL

from redpy.diffusers_custom import StableDiffusionCommonPipeline
from redpy.utils_redpy import get_basename_without_suffix
from redpy.diffusers_custom import add_textual_inversion, add_lora, draw_kps


def func_test():
    output_dir = '/share/wangqixun/workspace/tmp'
    base_model_path = '/share/xingchuan/code/diffusion/improved_sd/sd_diffusers/workspace/sam/sam_models'
    controlnet_path_list = [
        '/share/wangqixun/workspace/github_project/model_dl/sam_models-control-canny',
        '/share/wangqixun/workspace/github_project/model_dl/sam-control-depth',
    ]

    os.makedirs(output_dir, exist_ok=True)

    pipe = StableDiffusionCommonPipeline.from_pretrained(
        base_model_path,
        controlnet_list=controlnet_path_list,
        safety_checker=None,
        torch_dtype=torch.float16,
        feature_extractor=None,
    )
    pipe = pipe.to(torch.float16)
    pipe = pipe.to('cuda:0')

    img_input_dir = '/share/wangqixun/data/test_data/female_face'
    img_name_list = sorted(os.listdir(img_input_dir))

    client = DepthEstimationClient(
        ip='10.4.200.43',
        port='31002',
        max_send_message_length=100, 
        max_receive_message_length=100,
    )


    start_idx = 0
    for idx_img, img_name in enumerate(tqdm(img_name_list)):
        basename_without_suffix = get_basename_without_suffix(img_name)
        img_file = os.path.join(img_input_dir, img_name)
        input_image = Image.open(img_file).convert('RGB')
        w, h = input_image.size
        ratio = 512 / min(h, w)
        input_image = input_image.resize([int(ratio*w), int(ratio*h)])
        w, h = input_image.size
        ratio = 768 / max(h, w)
        input_image = input_image.resize([int(ratio*w), int(ratio*h)])
        control_image = np.array(input_image)
        low_threshold = 50
        high_threshold = 200
        control_image = cv2.Canny(control_image, low_threshold, high_threshold)
        control_image = np.concatenate([control_image[..., None]] * 3, axis=2)
        control_image = Image.fromarray(control_image)

        depth_img = client.run(np.array(input_image)[..., ::-1])
        depth_img = np.concatenate([depth_img[..., None]] * 3, axis=2)
        depth_img = Image.fromarray(depth_img)


        prompt = "sam yang, 1girl, backlighting, bare shoulders, black choker, blurry, blurry background, blush, breasts, choker, cleavage, closed mouth, collarbone, earrings, forehead, freckles, hair over shoulder, jewelry, long hair, looking down, pointy nose, red lips, shadow, solo, thick eyebrows, thick eyelashes, upper body, white hair , ((masterpiece)) <lora:sam_yang_offset:1>"
        negative_prompt = "(painting by bad-artist-anime:0.9), (painting by bad-artist:0.9), watermark, text, error, blurry, jpeg artifacts, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, artist name, (worst quality, low quality:1.4), bad anatomy"

        controlnet_conditioning = [
            dict(
                control_image=depth_img,
                control_index=1,
                control_weight=1.0,
            ),
            dict(
                control_image=control_image,
                control_index=0,
                control_weight=0.5,
            ),
        ]
        # controlnet_conditioning = []

        # img2img
        # image = pipe.img2img(
        #     image=input_image,
        #     controlnet_conditioning=controlnet_conditioning,
        #     strength=0.8,
        #     prompt=prompt,
        #     negative_prompt=negative_prompt,
        #     num_inference_steps=50,
        # ).images[0]
        # image_np = np.array(image)
        # input_image_np = np.array(input_image)
        # if image_np.shape != input_image_np.shape:
        #     image_np = cv2.resize(image_np, (input_image_np.shape[1], input_image_np.shape[0]))
        # image_np = np.concatenate([image_np, input_image_np], axis=1)
        # image = Image.fromarray(image_np)

        # text2img
        # image = pipe.text2img(
        #     controlnet_conditioning=controlnet_conditioning,
        #     prompt=prompt,
        #     negative_prompt=negative_prompt,
        #     height=768,
        #     width=512,
        #     num_inference_steps=50,
        # ).images[0]

        # inpatinting
        mask_image = np.zeros_like(input_image)
        mask_image[100:400, ] = 255
        mask_image = Image.fromarray(mask_image)
        image = pipe.inpatinting(
            image=input_image,
            mask_image=mask_image,
            controlnet_conditioning=controlnet_conditioning,
            prompt=prompt,
            negative_prompt=negative_prompt,
            # height=768,
            # width=512,
            num_inference_steps=50,
        ).images[0]
        image_np = np.array(image)
        input_image_np = np.array(input_image)
        if image_np.shape != input_image_np.shape:
            image_np = cv2.resize(image_np, (input_image_np.shape[1], input_image_np.shape[0]))
        image_np = np.concatenate([image_np, input_image_np], axis=1)
        image = Image.fromarray(image_np)

        image.save(f"{output_dir}/{basename_without_suffix}_{start_idx+idx_img:04d}.jpg")


def func_test_face():
    from PIL import Image
    generator = torch.manual_seed(0)
    from redpy.grpc import CommonClient
    # from redpy.grpc import DepthEstimationClient

    output_save_dir = '/share/wangqixun/workspace/tmp/face_control_tmp'
    # img_file = '/share/axe/datasets/xhs_selfie_hd/00000e4c-f389-3054-baaf-8003e61f4d5c.jpg'
    # img_file = '/share/wangqixun/workspace/github_project/redpy/test/data/touxiang.png'
    # img_file = '/share/wangqixun/data/test_data/djy_face/73341678608150_.pic_hd.jpg'
    img_file = '/share/wangqixun/workspace/business/face/data/dilireba_2.jpeg'

    # pretrained_model_name_or_path = '/share/wangqixun/workspace/github_project/diffusers/checkpoint/stable-diffusion-v1-5'
    pretrained_model_name_or_path = '/share/wangqixun/workspace/github_project/diffusers/checkpoint/pipeline_tmp'
    controlnet_path_list = [
        '/share/wangqixun/workspace/github_project/diffusers/checkpoint/pipeline_tmp-ControlNetModel',
        '/share/wangqixun/workspace/github_project/diffusers/checkpoint/pipeline_tmp-control_v11p_sd15_canny',
        # '/share/wangqixun/workspace/github_project/diffusers/checkpoint/controlnet/exp/face_conrtol_v3/ControlNetModel',
        # '/share/wangqixun/workspace/github_project/diffusers/checkpoint/controlnet/1-1/control_v11p_sd15_canny'
    ]
    textual_inversion_file = [
        '/share/wangqixun/workspace/github_project/diffusers/checkpoint/bad-picture-chill-75v.pt',
    ]
    lora_path_list = [
        # '/share/wangqixun/workspace/github_project/diffusers/checkpoint/eyeLora_eyesV10.safetensors',
        # '/share/wangqixun/workspace/github_project/diffusers/checkpoint/beautifulSky_beautifulSky.safetensors',
        # '/share/wangqixun/workspace/github_project/diffusers/checkpoint/beautifuleyeslikeness_halfBody.safetensors',
    ]

    controlnet_list = controlnet_path_list

    pipe = StableDiffusionCommonPipeline.from_pretrained(
        pretrained_model_name_or_path,
        controlnet_list=controlnet_list,
        safety_checker=None,
        feature_extractor=None,
    )
    # pipe = add_lora(lora_path_list, pipe, 0.6)
    # pipe, textual_inversion_tokens = add_textual_inversion(pipe, textual_inversion_file)
    pipe = pipe.cuda_half()


    image_raw = Image.open(img_file).convert('RGB')

    # w, h = image_raw.size
    # ratio = 448 / min(h, w)
    # image_raw = image_raw.resize([int(ratio*w), int(ratio*h)])
    w, h = image_raw.size
    ratio = 512 / max(h, w)
    image_raw = image_raw.resize([round(ratio*w), round(ratio*h)])
    client = CommonClient(
        ip='10.4.200.42',
        port='30390',
        max_send_message_length=100, 
        max_receive_message_length=100,
    )

    control_image_bgr = np.array(image_raw)[..., ::-1]
    face_info = client.run([control_image_bgr])[0]
    face_emb = face_info['embedding']
    face_kps = face_info['kps']
    control_image_face = draw_kps(image_raw, face_kps)

    control_image_canny = np.array(image_raw)
    low_threshold = 50
    high_threshold = 200
    control_image_canny = cv2.Canny(control_image_canny, low_threshold, high_threshold)
    control_image_canny = np.concatenate([control_image_canny[..., None]] * 3, axis=2)
    control_image_canny = Image.fromarray(control_image_canny)

    prompt = f'portrait of 25 years old young girl with white hair, looking at viewer, sunny, beach, sunny, sun'
    negative_prompt = f'canvas frame, cartoon, 3d, ((disfigured)), ((bad art)), ((deformed)),((extra limbs)),((close up)),'
    # prompt = "sam yang, 1girl, 3D, (depth of field:1.3), side lighting, thin eyebrow, backlighting, (blurry background), (blush:0.9), (freckles:0.0), earrings, forehead, jewelry, pointy nose, red lips, shadow, solo, masterpiece, (looking at viewer:1.2)"
    # negative_prompt = "(cross-eyed:1.2), nsfw, painting by bad-artist-anime, painting by bad-artist, watermark, text, error, blurry, jpeg artifacts, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, artist name, worst quality, low quality, bad anatomy"

    idx_start = 366
    for iii in range(idx_start, idx_start+6, 1):
        controlnet_conditioning = [
            dict(
                control_image=control_image_face,
                control_index=0,
                control_weight=1.,
                control_visual_emb=face_emb,
            ),
            dict(
                control_image=control_image_canny,
                control_index=1,
                control_weight=0.8,
            ),
            # dict(
            #     control_image=depth_img,
            #     control_index=2,
            #     control_weight=0.5,
            # ),
        ]

        image = pipe.text2img(
            controlnet_conditioning=controlnet_conditioning,
            prompt=prompt,
            negative_prompt=negative_prompt,
            guidance_scale=5.5,
            # height=512,
            # width=512,
            num_inference_steps=50,
            generator=generator,
        ).images[0]

        # image = pipe.img2img(
        #     image=image_raw,
        #     strength=0.6,
        #     controlnet_conditioning=controlnet_conditioning,
        #     prompt=prompt,
        #     negative_prompt=negative_prompt,
        #     guidance_scale=7.5,
        #     num_inference_steps=50,
        #     generator=generator,
        # ).images[0]


        raw_image = Image.open(img_file).convert('RGB').resize((image.width, image.height))
        image = Image.fromarray(np.concatenate([np.array(image), np.array(raw_image)], axis=0))
        image.save(os.path.join(output_save_dir, f"{iii:04d}.jpg"))

    for iii in range(idx_start+6, idx_start+6+6, 1):
        controlnet_conditioning = [
            dict(
                control_image=control_image_face,
                control_index=0,
                control_weight=1.,
                control_visual_emb=face_emb,
            ),
            dict(
                control_image=control_image_canny,
                control_index=1,
                control_weight=0.8,
            ),
            # dict(
            #     control_image=depth_img,
            #     control_index=2,
            #     control_weight=0.5,
            # ),
        ]

        # image = pipe.text2img(
        #     controlnet_conditioning=controlnet_conditioning,
        #     prompt=prompt,
        #     negative_prompt=negative_prompt,
        #     guidance_scale=7.5,
        #     # height=512,
        #     # width=512,
        #     num_inference_steps=50,
        #     generator=generator,
        # ).images[0]

        image = pipe.img2img(
            image=image_raw,
            strength=0.6,
            controlnet_conditioning=controlnet_conditioning,
            prompt=prompt,
            negative_prompt=negative_prompt,
            guidance_scale=5.5,
            num_inference_steps=50,
            generator=generator,
        ).images[0]


        raw_image = Image.open(img_file).convert('RGB').resize((image.width, image.height))
        image = Image.fromarray(np.concatenate([np.array(image), np.array(raw_image)], axis=0))
        image.save(os.path.join(output_save_dir, f"{iii:04d}.jpg"))


def face_for_antong():
    from PIL import Image
    from redpy.diffusers_custom import add_textual_inversion, add_lora, draw_kps
    generator = torch.manual_seed(0)
    from redpy.grpc import CommonClient

    # 配置文件
    output_dir = '/share/wangqixun/workspace/tmp_zhishuzaolin'
    base_model_path = '/share/xingchuan/code/diffusion/improved_sd/sd_diffusers/workspace/sam/sam_models'
    controlnet_path_list = [
        '/share/wangqixun/workspace/github_project/diffusers/checkpoint/sam-control-face',
        # '/share/wangqixun/workspace/github_project/model_dl/sam_models-control-canny',
        '/share/wangqixun/workspace/github_project/model_dl/sam-control_v11p_sd15_canny',
        '/share/wangqixun/workspace/github_project/model_dl/sam-control-depth',
    ]
    lora_path_list = [
        # '/share/wangqixun/workspace/github_project/diffusers/checkpoint/beautifulSky_beautifulSky.safetensors',
        '/share/wangqixun/workspace/github_project/diffusers/checkpoint/beautifuleyeslikeness_halfBody.safetensors',
    ]

    # face client
    client_face = CommonClient(
        ip='10.4.200.42',
        port='30390',
        max_send_message_length=100, 
        max_receive_message_length=100,
    )
    # depth client
    client_depth = CommonClient(
        ip='10.4.200.42',
        port='30301',
        max_send_message_length=100, 
        max_receive_message_length=100,
    )

    # pipeline部分
    pipe = StableDiffusionCommonPipeline.from_pretrained(
        base_model_path,
        controlnet_list=controlnet_path_list,
        safety_checker=None,
        feature_extractor=None,
    )
    pipe = add_lora(lora_path_list, pipe, 0.4)
    pipe = pipe.cuda_half()


    # 用户图像
    img_file = '/share/axe/xhs_selfie_hd/00000e4c-f389-3054-baaf-8003e61f4d5c.jpg'
    image_raw = Image.open(img_file).convert('RGB')
    w, h = image_raw.size
    ratio = 512 / max(h, w)
    image_raw = image_raw.resize([round(ratio*w), round(ratio*h)])

    # 输出多张
    idx_start = 0
    for idx_image in range(idx_start, idx_start+18, 1):
        # control info - face
        control_image_bgr = np.array(image_raw)[..., ::-1]
        face_info = client_face.run([control_image_bgr])[0]
        face_emb = face_info['embedding']
        face_kps = face_info['kps']
        control_image_face = draw_kps(image_raw, face_kps)

        # control info - canny
        control_image_canny = np.array(image_raw)
        low_threshold = 50
        high_threshold = 200
        control_image_canny = cv2.Canny(control_image_canny, low_threshold, high_threshold)
        control_image_canny = np.concatenate([control_image_canny[..., None]] * 3, axis=2)
        control_image_canny = Image.fromarray(control_image_canny)

        # control info - canny
        depth_img = client_depth.run([np.array(image_raw)[..., ::-1]])
        depth_img = np.concatenate([depth_img[..., None]] * 3, axis=2)
        depth_img = Image.fromarray(depth_img)


        # infer
        prompt = "sam yang, 1girl, (yellow hair:1.1), (blue eyes:1.1), earring, 3D, (depth of field:1.3), side lighting, thin eyebrow, backlighting, (blurry background), (blush:0.9), (freckles:0.0), earrings, forehead, jewelry, pointy nose, red lips, shadow, solo, masterpiece, (looking at viewer:1.2)"
        negative_prompt = f"(cross-eyed:1.2), nsfw, painting by bad-artist-anime, painting by bad-artist, watermark, text, error, blurry, jpeg artifacts, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, artist name, worst quality, low quality, bad anatomy"
        # negative_prompt = f"({textual_inversion_tokens[1]}:0.8) (cross-eyed:1.2), nsfw, painting by bad-artist-anime, painting by bad-artist, watermark, text, error, blurry, jpeg artifacts, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, artist name, worst quality, low quality, bad anatomy"
        controlnet_conditioning = [
            dict(
                control_image=control_image_face,
                control_index=0,
                control_weight=1.0,
                control_visual_emb=face_emb,
            ),
            dict(
                control_image=control_image_canny,
                control_index=1,
                control_weight=0.8,
            ),
            # dict(
            #     control_image=depth_img,
            #     control_index=2,
            #     control_weight=0.5,
            # ),
        ]

        # image = pipe.text2img(
        #     controlnet_conditioning=controlnet_conditioning,
        #     prompt=prompt,
        #     negative_prompt=negative_prompt,
        #     guidance_scale=7.5,
        #     # height=512,
        #     # width=512,
        #     num_inference_steps=50,
        #     generator=generator,
        # ).images[0]

        image = pipe.img2img(
            image=image_raw,
            strength=0.85,
            controlnet_conditioning=controlnet_conditioning,
            prompt=prompt,
            negative_prompt=negative_prompt,
            guidance_scale=7.5,
            num_inference_steps=50,
            generator=generator,
        ).images[0]

        raw_image = Image.open(img_file).convert('RGB').resize((image.width, image.height))
        image = Image.fromarray(np.concatenate([np.array(image), np.array(raw_image)], axis=0))
        image.save(os.path.join(output_dir, f"{idx_image:04d}.jpg"))


def face_shuffle():
    from PIL import Image
    from redpy.diffusers_custom import add_textual_inversion, add_lora, draw_kps
    generator = torch.manual_seed(0)
    from redpy.grpc import CommonClient
    # from redpy.grpc import DepthEstimationClient
    from controlnet_aux import ContentShuffleDetector

    output_save_dir = '/share/wangqixun/workspace/tmp/face_control_tmp'
    img_file = '/share/axe/xhs_selfie_hd/00000e4c-f389-3054-baaf-8003e61f4d5c.jpg'
    # img_file = '/share/wangqixun/workspace/github_project/redpy/test/data/touxiang.png'
    # img_file = '/share/wangqixun/data/test_data/djy_face/73341678608150_.pic_hd.jpg'

    pretrained_model_name_or_path = '/share/wangqixun/workspace/github_project/diffusers/checkpoint/stable-diffusion-v1-5'
    controlnet_path_list = [
        # '/share/wangqixun/workspace/github_project/diffusers/checkpoint/controlnet/sd-controlnet-face',
        '/share/wangqixun/workspace/github_project/diffusers/checkpoint/controlnet/exp/face_conrtol_v3/ControlNetModel',
        '/share/wangqixun/workspace/github_project/diffusers/checkpoint/sd-controlnet-canny',
        # '/share/wangqixun/workspace/github_project/diffusers/checkpoint/sam-control-face',
        # '/share/wangqixun/workspace/github_project/model_dl/sam_models-control-canny',
        # '/share/wangqixun/workspace/github_project/model_dl/sam-control-depth',
        # '/share/wangqixun/workspace/github_project/diffusers/checkpoint/sd-controlnet-canny',
        '/share/wangqixun/workspace/github_project/diffusers/checkpoint/controlnet/1-1/control_v11e_sd15_shuffle'
    ]
    textual_inversion_file = [
        '/share/wangqixun/workspace/github_project/diffusers/checkpoint/bad-picture-chill-75v.pt'
    ]
    lora_path_list = [
        '/share/wangqixun/workspace/github_project/diffusers/checkpoint/beautifulSky_beautifulSky.safetensors',
        '/share/wangqixun/workspace/github_project/diffusers/checkpoint/beautifuleyeslikeness_halfBody.safetensors',
    ]

    controlnet_list = controlnet_path_list

    pipe = StableDiffusionCommonPipeline.from_pretrained(
        pretrained_model_name_or_path,
        controlnet_list=controlnet_list,
        safety_checker=None,
        feature_extractor=None,
    )
    pipe = add_lora(lora_path_list, pipe, 0.6)
    pipe, textual_inversion_tokens = add_textual_inversion(pipe, textual_inversion_file)
    pipe = pipe.cuda_half()


    image_raw = Image.open(img_file).convert('RGB')

    # w, h = image_raw.size
    # ratio = 448 / min(h, w)
    # image_raw = image_raw.resize([int(ratio*w), int(ratio*h)])
    w, h = image_raw.size
    ratio = 512 / max(h, w)
    image_raw = image_raw.resize([round(ratio*w), round(ratio*h)])
    client = CommonClient(
        ip='10.4.200.42',
        port='30390',
        max_send_message_length=100, 
        max_receive_message_length=100,
    )
    processor = ContentShuffleDetector()

    control_image_shuffle = processor(image_raw)

    control_image_bgr = np.array(image_raw)[..., ::-1]
    face_info = client.run([control_image_bgr])[0]
    face_emb = face_info['embedding']
    face_kps = face_info['kps']
    control_image_face = draw_kps(image_raw, face_kps)

    control_image_canny = np.array(image_raw)
    low_threshold = 50
    high_threshold = 200
    control_image_canny = cv2.Canny(control_image_canny, low_threshold, high_threshold)
    control_image_canny = np.concatenate([control_image_canny[..., None]] * 3, axis=2)
    control_image_canny = Image.fromarray(control_image_canny)

    idx_start = 156
    for iii in range(idx_start, idx_start+6, 1):
        prompt = f'portrait of 25 years old girl with (white hair:1.1), looking at viewer, sky, big eye'
        negative_prompt = f'canvas frame, cartoon, 3d, ((disfigured)), ((bad art)), ((deformed)),((extra limbs)),((close up)),'
        # prompt = "sam yang, 1girl, 3D, (depth of field:1.3), side lighting, thin eyebrow, backlighting, (blurry background), (blush:0.9), (freckles:0.0), earrings, forehead, jewelry, pointy nose, red lips, shadow, solo, masterpiece, (looking at viewer:1.2)"
        # negative_prompt = "(cross-eyed:1.2), nsfw, painting by bad-artist-anime, painting by bad-artist, watermark, text, error, blurry, jpeg artifacts, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, artist name, worst quality, low quality, bad anatomy"

        controlnet_conditioning = [
            dict(
                control_image=control_image_shuffle,
                control_index=2,
                control_weight=1.0,
            ),
        ]
        image = pipe.img2img(
            image=image_raw,
            strength=0.85,
            controlnet_conditioning=controlnet_conditioning,
            prompt=prompt,
            negative_prompt=negative_prompt,
            guidance_scale=7.5,
            num_inference_steps=50,
            generator=generator,
        ).images[0]

        control_image_bgr = np.array(image)[..., ::-1]
        face_info = client.run([control_image_bgr])[0]
        face_emb = face_emb
        face_kps = face_info['kps']
        control_image_face = draw_kps(image_raw, face_kps)

        
        controlnet_conditioning = [
            dict(
                control_image=control_image_face,
                control_index=0,
                control_weight=1.0,
                control_visual_emb=face_emb,
            ),
            # dict(
            #     control_image=control_image_canny,
            #     control_index=1,
            #     control_weight=0.25,
            # ),
            # dict(
            #     control_image=depth_img,
            #     control_index=2,
            #     control_weight=0.5,
            # ),
            dict(
                control_image=control_image_shuffle,
                control_index=2,
                control_weight=1.0,
            ),
        ]

        image = pipe.text2img(
            controlnet_conditioning=controlnet_conditioning,
            prompt=prompt,
            negative_prompt=negative_prompt,
            guidance_scale=7.5,
            # height=512,
            # width=512,
            num_inference_steps=50,
            generator=generator,
        ).images[0]

        # image = pipe.img2img(
        #     image=image_raw,
        #     strength=0.85,
        #     controlnet_conditioning=controlnet_conditioning,
        #     prompt=prompt,
        #     negative_prompt=negative_prompt,
        #     guidance_scale=7.5,
        #     num_inference_steps=50,
        #     generator=generator,
        # ).images[0]


        raw_image = Image.open(img_file).convert('RGB').resize((image.width, image.height))
        image = Image.fromarray(np.concatenate([np.array(image), np.array(raw_image)], axis=0))
        image.save(os.path.join(output_save_dir, f"{iii:04d}.jpg"))



if __name__ == '__main__':
    # func_test()
    func_test_face()
    # face_for_antong()
    # face_shuffle()