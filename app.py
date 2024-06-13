import os
import json
import base64
import boto3
import streamlit as st
from io import BytesIO
from botocore.exceptions import ClientError
from streamlit_cognito_auth import authenticate, logout_user

# Initialize AWS clients
session = boto3.Session(profile_name='default')
bedrock_client = session.client('bedrock-runtime')
s3 = session.client('s3')

# Cognito authentication
user = authenticate(
    cognito_user_pool_id="us-east-1_8k4Xn6O8h",
    cognito_user_pool_client_id="7mo5kmp9jb0f9h4o8rvbe3dtdk",
    cognito_user_pool_domain="3.92.174.125:8501",
)

if user is None:
    st.error("Please sign in to continue.")
else:
    # Streamlit app
    st.title("Amazon Bedrock Titan Image Generator 1.0")

    prompt = st.text_input("Enter a prompt to generate an image:")
    seed = st.number_input("Enter a seed value:", min_value=0, step=1)

    if st.button("Generate Image"):
        try:
            # Invoke the Titan Image Generator model
            response = bedrock_client.invoke_model(
                modelId="amazon.titan-image-generator-v1",
                contentType="application/json",
                accept="application/json",
                body=bytes(f'{{"textToImageParams":{{"text":"{prompt}"}},"taskType":"TEXT_IMAGE","imageGenerationConfig":{{"cfgScale":8,"seed":{seed},"quality":"standard","width":1024,"height":1024,"numberOfImages":3}}}}'.encode('utf-8'))
            )

            # Get the generated images
            response_body = json.loads(response.get("body").read())
            images = response_body.get("images")

            # Display the images
            col1, col2, col3 = st.columns(3)
            with col1:
                base64_image = images[0]
                base64_bytes = base64_image.encode('ascii')
                image_bytes = base64.b64decode(base64_bytes)
                st.image(image_bytes, caption=f"{prompt} (1)", use_column_width=True)

            with col2:
                base64_image = images[1]
                base64_bytes = base64_image.encode('ascii')
                image_bytes = base64.b64decode(base64_bytes)
                st.image(image_bytes, caption=f"{prompt} (2)", use_column_width=True)

            with col3:
                base64_image = images[2]
                base64_bytes = base64_image.encode('ascii')
                image_bytes = base64.b64decode(base64_bytes)
                st.image(image_bytes, caption=f"{prompt} (3)", use_column_width=True)

            # Save the images to S3
            for i, image_data in enumerate(images):
                base64_bytes = image_data.encode('ascii')
                image_bytes = base64.b64decode(base64_bytes)
                bucket_name = "adtech-images-bucket"
                object_key = f"{prompt.replace(' ', '_')}_{i+1}.png"
                s3.put_object(Bucket=bucket_name, Key=object_key, Body=image_bytes)
                st.success(f"Image {i+1} saved to S3 at s3://{bucket_name}/{object_key}")

        except ClientError as e:
            st.error(f"Error generating image: {e}")

    # Add a logout button
    if st.button("Logout"):
        logout_user()
