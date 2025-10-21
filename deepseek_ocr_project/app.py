import streamlit as st
import torch
from transformers import AutoProcessor, AutoModel
from PIL import Image
import requests
import io
import base64

# Page configuration
st.set_page_config(
    page_title="DeepSeek OCR Analysis",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        color: #1f77b4;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 3rem;
    }
    .result-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
    }
    .confidence-bar {
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_model():
    """Load the DeepSeek OCR model and processor"""
    try:
        model_name = "deepseek-ai/DeepSeek-OCR"
        processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
        model = AutoModel.from_pretrained(model_name, trust_remote_code=True, use_safetensors=True)

        # Use CPU since CUDA is not available on this system
        device = "cpu"
        model = model.to(device).to(torch.bfloat16)

        return processor, model, device
    except Exception as e:
        st.error(f"Error loading model: {str(e)}")
        return None, None, None

def process_image(image, processor, model, device):
    """Process image through DeepSeek OCR model"""
    try:
        # Prepare inputs for the vision-language model
        prompt = "Extract all text from this image and convert it to markdown format."

        # Process the image and text together
        inputs = processor(
            text=prompt,
            images=image,
            return_tensors="pt"
        )

        # Move inputs to the same device as the model
        inputs = {k: v.to(device) for k, v in inputs.items()}

        # Generate text using the model's generate method
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=512,
                do_sample=True,
                temperature=0.7
            )

        # Decode the generated text
        generated_text = processor.batch_decode(outputs, skip_special_tokens=True)[0]

        # Clean up the generated text (remove the original prompt if present)
        if prompt in generated_text:
            generated_text = generated_text.replace(prompt, "").strip()

        return generated_text if generated_text else "No text was extracted from the image."

    except Exception as e:
        import traceback
        return f"Error processing image: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"

def download_image(url):
    """Download image from URL"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Ensure we have valid image content
        content = response.content
        if not content:
            raise ValueError("Empty response content")

        # Create BytesIO object and open as image
        image_buffer = io.BytesIO(content)
        image = Image.open(image_buffer)

        # Verify the image is valid by checking its format
        image.verify()
        image = Image.open(io.BytesIO(content))  # Re-open after verify

        return image
    except Exception as e:
        st.error(f"Error downloading image: {str(e)}")
        return None

def main():
    # Header
    st.markdown('<div class="main-header">🔍 DeepSeek OCR Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Analyze images using DeepSeek\'s advanced OCR model</div>', unsafe_allow_html=True)

    # Load model
    with st.spinner("Loading DeepSeek OCR model... This may take a moment."):
        processor, model, device = load_model()

    if processor is None:
        st.error("Failed to load the model. Please check your internet connection and try again.")
        return

    # Sidebar
    st.sidebar.title("📋 Options")
    st.sidebar.markdown("---")

    # Input method selection
    input_method = st.sidebar.radio(
        "Choose input method:",
        ["Upload Image", "Image URL", "Sample Images"]
    )

    # Main content area
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📸 Input")

        if input_method == "Upload Image":
            uploaded_file = st.file_uploader(
                "Choose an image file",
                type=["png", "jpg", "jpeg", "bmp", "tiff"],
                help="Upload an image containing text to analyze"
            )

            if uploaded_file is not None:
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Image")

        elif input_method == "Image URL":
            image_url = st.text_input(
                "Enter image URL:",
                placeholder="https://example.com/image.jpg",
                help="Enter a direct link to an image"
            )

            if image_url and st.button("Load Image"):
                image = download_image(image_url)
                if image:
                    st.image(image, caption=f"Image from URL: {image_url}")
            else:
                image = None

        else:  # Sample Images
            sample_options = {
                "Text Document": "https://www.dropbox.com/scl/fi/0o0c7c8j8c8j8c8j8c8j8c8j8/sample_text.jpg?rlkey=abc123",
                "Mixed Content": "https://www.dropbox.com/scl/fi/0o0c7c8j8c8j8c8j8c8j8c8j8/sample_mixed.jpg?rlkey=def456",
                "Handwriting": "https://www.dropbox.com/scl/fi/0o0c7c8j8c8j8c8j8c8j8c8j8/sample_handwriting.jpg?rlkey=ghi789"
            }

            selected_sample = st.selectbox(
                "Choose a sample image:",
                list(sample_options.keys())
            )

            if st.button("Load Sample Image"):
                image = download_image(sample_options[selected_sample])
                if image:
                    st.image(image, caption=f"Sample Image: {selected_sample}")
            else:
                image = None

    with col2:
        st.subheader("📝 Analysis Results")

        if input_method == "Upload Image" and 'uploaded_file' in locals() and uploaded_file is not None:
            if st.button("🔍 Analyze Image", type="primary"):
                with st.spinner("Analyzing image..."):
                    result = process_image(image, processor, model, device)
                    st.markdown('<div class="result-box">', unsafe_allow_html=True)
                    st.markdown("**Extracted Text:**")
                    st.write(result)
                    st.markdown('</div>', unsafe_allow_html=True)

        elif input_method == "Image URL" and 'image' in locals() and image is not None:
            if st.button("🔍 Analyze Image", type="primary"):
                with st.spinner("Analyzing image..."):
                    result = process_image(image, processor, model, device)
                    st.markdown('<div class="result-box">', unsafe_allow_html=True)
                    st.markdown("**Extracted Text:**")
                    st.write(result)
                    st.markdown('</div>', unsafe_allow_html=True)

        elif input_method == "Sample Images" and 'image' in locals() and image is not None:
            if st.button("🔍 Analyze Image", type="primary"):
                with st.spinner("Analyzing image..."):
                    result = process_image(image, processor, model, device)
                    st.markdown('<div class="result-box">', unsafe_allow_html=True)
                    st.markdown("**Extracted Text:**")
                    st.write(result)
                    st.markdown('</div>', unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
        <p>Powered by <strong>DeepSeek OCR</strong> from Hugging Face</p>
        <p>Model: deepseek-ai/DeepSeek-OCR</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
