import os
import base64

from dotenv import load_dotenv
import openai

load_dotenv()

# set password to None if using API key
openai.api_key = os.getenv("OPENAI_KEY")
if openai.api_key is None:
    raise ValueError("API key not found. Please provide an API key or add it to the .env file")


def image_inference(prompt: str, image_path: str) -> str:
    """
    Infer with an image and a text prompt.

    @param prompt: Text prompt for the model.
    @param image_path: Path to the image file.
    @return: Model response to the prompt and image.
    @throws ValueError: If the image format is not .png or .jpeg.
    """

    # check if image ends with .png or .jpg
    image_format = image_path.split(".")[-1]
    if image_format not in ["png", "jpg"]:
        raise ValueError("Image format must be either .png or .jpeg")

    # encode image as base64
    with open(image_path, "rb") as image:
        image_base64 = base64.b64encode(image.read()).decode("utf-8")

    # infer with low resolution image (2833 tokens ~512x512 pixels image?)
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{image_format};base64,{image_base64}",
                            "detail": "low",
                        },
                    },
                ],
            }
        ],
    )

    usage = {"input": response.usage.prompt_tokens, "output": response.usage.completion_tokens}
    usage["cost"] = round((0.15 * usage["input"] + 0.6 * usage["output"]) / 1e4, 3)
    content = "\n".join([choice.message.content for choice in response.choices])

    return content, usage
