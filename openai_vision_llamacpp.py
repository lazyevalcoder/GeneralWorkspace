# 1. Importing necessary libraries
from openai import OpenAI
import base64

# 2. Setting up the API
client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama',  # required, but unused
)

# 3. Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

image_path = "Images/McKinsey-Global-Payments.jpg"
base64_image = encode_image(image_path)

# 4. Constructing the payload
payload = {
    "model": "minicpm-v:8b-2.6-q8_0",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Explain what's in this slide in English"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
        }
    ],
}

# 5. Using the openai library to send the request
response = client.chat.completions.create(**payload)

# 6. Print the response
print(response)
