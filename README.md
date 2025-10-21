# DeepSeek OCR Analysis App

A Streamlit web application for analyzing images using DeepSeek's advanced OCR model from Hugging Face.

## Features

- 🔍 **Multiple Input Methods**: Upload images, use image URLs, or try sample images
- 🤖 **DeepSeek OCR Model**: Powered by `deepseek-ai/DeepSeek-OCR` from Hugging Face
- 🎨 **Modern UI**: Clean, responsive interface with custom styling
- ⚡ **GPU Support**: Automatically uses CUDA if available for faster processing
- 📱 **Responsive Design**: Works on desktop and mobile devices

## Installation

1. **Clone or download the project files**
   ```bash
   # Make sure you have the required files:
   # - app.py
   # - requirements.txt
   # - README.md
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run app.py
   ```

4. **Open your browser**
   Navigate to `http://localhost:8501` to access the application.

## Usage

### Input Methods

1. **Upload Image**: Click "Browse files" to upload an image from your computer
2. **Image URL**: Enter a direct link to an image and click "Load Image"
3. **Sample Images**: Choose from pre-configured sample images for testing

### Supported Image Formats

- PNG
- JPG/JPEG
- BMP
- TIFF

### Sample Images Performance

The application includes three sample images to demonstrate OCR capabilities:

#### 📄 Text Document (sample_text.jpg)
- **Content**: Clean printed text document
- **Expected Results**: Excellent accuracy (95%+)
- **Use Case**: Testing basic OCR functionality with clear text
- **Processing Time**: Fast (< 10 seconds)

#### 🔗 Mixed Content (sample_mixed.jpg)
- **Content**: Document with text, tables, and graphics
- **Expected Results**: Good accuracy (85-95%)
- **Use Case**: Testing mixed content extraction
- **Processing Time**: Moderate (10-20 seconds)
- **Challenges**: May have minor formatting issues with complex layouts

#### ✍️ Handwriting (sample_handwriting.jpg)
- **Content**: Handwritten notes or documents
- **Expected Results**: Variable accuracy (70-90%)
- **Use Case**: Testing handwriting recognition capabilities
- **Processing Time**: Moderate (10-20 seconds)
- **Challenges**: Depends on handwriting clarity and style

### How to Use

1. Select your preferred input method from the sidebar
2. Provide the image (upload, URL, or select sample)
3. Click "🔍 Analyze Image" to process the image
4. View the extracted text in the results section

### Performance Tips for Best Results

- **Clear Images**: Higher resolution and good lighting improve accuracy
- **Simple Layouts**: Documents with clear structure work better
- **Standard Fonts**: Common fonts are recognized more accurately than decorative ones
- **Good Contrast**: Black text on white background yields best results

## Model Information

- **Model**: `deepseek-ai/DeepSeek-OCR`
- **Framework**: Transformers (Hugging Face)
- **Device**: Automatically uses GPU (CUDA) if available, otherwise CPU
- **Max Tokens**: 512 tokens per analysis

## Requirements

- Python 3.8+
- Streamlit >= 1.28.0
- PyTorch >= 2.0.0
- Transformers >= 4.35.0
- Pillow >= 10.0.0
- Requests >= 2.31.0

## Performance Tips

- **First Load**: Model loading may take several minutes on first run
- **GPU Acceleration**: Significantly faster processing if CUDA is available
- **Image Size**: Smaller images process faster but may reduce accuracy
- **Internet Connection**: Required for initial model download

## Troubleshooting

### Common Issues

1. **Model loading fails**
   - Check internet connection
   - Ensure sufficient disk space (~2GB for model)
   - Try restarting the application

2. **CUDA errors**
   - Ensure PyTorch with CUDA support is installed
   - Check GPU compatibility
   - Falls back to CPU automatically

3. **Memory errors**
   - Close other applications
   - Use smaller images
   - Restart the application

### Getting Help

If you encounter issues:
1. Check the terminal output for error messages
2. Ensure all dependencies are installed correctly
3. Verify your Python version compatibility

## License

This project is for educational and demonstration purposes. The DeepSeek OCR model is provided by DeepSeek AI and is subject to their terms of use.

## Contributing

Feel free to submit issues and enhancement requests!
