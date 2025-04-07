import io
import os
import tempfile

import openai
import pymupdf
import streamlit as st
from dotenv import load_dotenv
from PIL import Image

# Import our custom utilities
from finalcheck.utils import (
    CHECK_CRITERIA,
    analyze_page_with_vision_api,
    generate_summary_report,
)

# Load environment variables
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")


# Function to extract pages from PDF using PyMuPDF
def extract_pages(pdf_file, dpi=300):
    # Write the uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(pdf_file.getvalue())
        temp_pdf_path = temp_pdf.name

    # Open the PDF with PyMuPDF
    pdf_document = pymupdf.open(temp_pdf_path)

    # Convert pages to images
    images = []

    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap(dpi=dpi).tobytes("jpeg")

        # Convert PyMuPDF pixmap to PIL Image
        img = Image.open(io.BytesIO(pix))
        img.save("page.jpg")
        images.append(img)

    # Close the PDF
    pdf_document.close()

    # Clean up temporary file
    os.unlink(temp_pdf_path)

    return images


def process_pdf(pdf_file, dpi=90):
    """Process PDF file and return list of PIL Images"""
    # Write the uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(pdf_file.getvalue())
        temp_pdf_path = temp_pdf.name

    # Open the PDF with PyMuPDF
    pdf_document = pymupdf.open(temp_pdf_path)

    # Convert pages to images
    images = []
    zoom = dpi / 72  # PyMuPDF uses 72 dpi as base
    mat = pymupdf.Matrix(zoom, zoom)

    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap(matrix=mat)

        # Convert PyMuPDF pixmap to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)

    # Close the PDF
    pdf_document.close()

    # Clean up temporary file
    os.unlink(temp_pdf_path)

    return images


def process_image(image_file):
    """Process single image file and return as PIL Image"""
    return Image.open(image_file)


def main():
    # App configuration
    st.set_page_config(
        page_title="FinalCheck - PDF Compliance Verification",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Create sidebar
    with st.sidebar:
        st.title("FinalCheck")
        st.markdown("### PDF Compliance Verification")
        st.markdown(
            "Upload a PDF or image file and select which compliance checks to perform."
        )

        # Add info about the app
        with st.expander("About this app"):
            st.markdown("""
            This application helps verify PDF documents for compliance with specific requirements:
            
            - **File Upload**: Upload PDF (max 10MB) or image file
            - **Controlled Verification**: Select specific checks to perform
            - **AI-Powered Analysis**: Uses vision AI to analyze content
            - **Compliance Report**: View detailed compliance status
            """)

        # Add info about the checks
        with st.expander("Available Compliance Checks"):
            for check_id, criteria in CHECK_CRITERIA.items():
                st.markdown(f"**{check_id}**")
                st.markdown(f"{criteria['description']}")
                st.markdown("---")

    # Main area
    st.title("PDF Compliance Verification")

    # File upload section
    st.subheader("Upload File")
    file_type = st.radio(
        "Select file type to upload:",
        ["PDF Document", "Single Image"],
        help="Choose whether to upload a PDF document or a single image file",
    )

    if file_type == "PDF Document":
        uploaded_file = st.file_uploader(
            "Upload a PDF file", type="pdf", help="Maximum file size: 10MB"
        )
    else:  # Single Image
        uploaded_file = st.file_uploader(
            "Upload an image file",
            type=["png", "jpg", "jpeg"],
            help="Supported formats: PNG, JPG, JPEG",
        )

    # Check options using the criteria from utils
    st.subheader("Select Compliance Checks")

    col1, col2 = st.columns(2)
    selected_checks = {}

    # Create checkboxes in two columns
    check_ids = list(CHECK_CRITERIA.keys())
    half = len(check_ids) // 2 + len(check_ids) % 2

    with col1:
        for check_id in check_ids[:half]:
            criteria = CHECK_CRITERIA[check_id]
            selected_checks[check_id] = st.checkbox(
                criteria["description"], value=True, key=f"check_{check_id}"
            )

    with col2:
        for check_id in check_ids[half:]:
            criteria = CHECK_CRITERIA[check_id]
            selected_checks[check_id] = st.checkbox(
                criteria["description"], value=True, key=f"check_{check_id}"
            )

    # Get active checks
    active_checks = [
        check_id for check_id, is_selected in selected_checks.items() if is_selected
    ]

    # Process uploaded file
    if uploaded_file is not None:
        # Check file size (10MB limit)
        if uploaded_file.size > 10 * 1024 * 1024:
            st.error("File size exceeds the 10MB limit. Please upload a smaller file.")
        else:
            # Display file info
            st.write(
                f"File uploaded: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)"
            )

            # Process button
            if st.button("Analyze File", type="primary"):
                if not active_checks:
                    st.warning(
                        "Please select at least one compliance check to perform."
                    )
                else:
                    # Create session state for storing results if not exists
                    if "page_results" not in st.session_state:
                        st.session_state.page_results = []

                    with st.spinner("Processing file..."):
                        # Process file based on type
                        if file_type == "PDF Document":
                            images = process_pdf(uploaded_file)
                            st.success(
                                f"✅ Successfully extracted {len(images)} pages from the PDF."
                            )
                        else:
                            images = [process_image(uploaded_file)]
                            st.success("✅ Successfully processed the image.")

                        # Create tabs for the workflow
                        tab1, tab2, tab3 = st.tabs(
                            ["File Preview", "Analysis", "Compliance Report"]
                        )

                        # Tab 1: Preview
                        with tab1:
                            st.subheader("File Preview")

                            if len(images) > 1:
                                # Display a grid of page thumbnails for PDF
                                cols = st.columns(4)
                                for i, img in enumerate(images):
                                    with cols[i % 4]:
                                        st.image(
                                            img, caption=f"Page {i + 1}", width=150
                                        )
                            else:
                                # Display single image
                                st.image(images[0], caption="Uploaded Image", width=400)

                        # Tab 2: Analyze with progress bar
                        with tab2:
                            st.subheader("Analysis")

                            # Reset results
                            st.session_state.page_results = []

                            # Create a progress bar
                            progress_bar = st.progress(0)
                            status_text = st.empty()

                            # Process each image
                            for i, img in enumerate(images):
                                # Update progress
                                progress = (i + 1) / len(images)
                                progress_bar.progress(progress)
                                status_text.text(
                                    f"Analyzing image {i + 1} of {len(images)}..."
                                )

                                # Analyze the image
                                page_result = analyze_page_with_vision_api(
                                    img, active_checks
                                )

                                # Store the result
                                st.session_state.page_results.append(
                                    {
                                        "page_number": i + 1,
                                        "results": page_result,
                                    }
                                )

                            # Complete the progress
                            progress_bar.progress(1.0)
                            status_text.text("✅ Analysis complete!")

                            # Display individual results
                            st.subheader("Analysis Results")
                            for page_data in st.session_state.page_results:
                                with st.expander(
                                    f"{'Page' if len(images) > 1 else 'Image'} {page_data['page_number']}"
                                ):
                                    if "results" in page_data:
                                        for check_result in page_data["results"]:
                                            st.markdown(
                                                f"### {check_result.get('standard_name', 'Unknown Standard')}"
                                            )

                                            # Show compliance status with color
                                            is_compliant = check_result.get(
                                                "is_compliant", False
                                            )
                                            if is_compliant:
                                                st.markdown("✅ **Compliant**")
                                            else:
                                                st.markdown("❌ **Non-Compliant**")
                                            st.markdown(
                                                f"**Content Description:** \n\n {check_result.get('content_description', 'No content description available')}"
                                            )

                                    else:
                                        st.error("No analysis results available.")

                        # Tab 3: Overall compliance report
                        with tab3:
                            st.subheader("Compliance Report")

                            # Generate summary report
                            summary = generate_summary_report(
                                st.session_state.page_results
                            )

                            # Display overall compliance
                            if summary["overall_compliance"]:
                                st.success(
                                    "✅ File is compliant with all selected standards."
                                )
                            else:
                                st.error(
                                    "❌ File does not comply with all selected standards."
                                )

                            # Show compliance metrics
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total Images/Pages", summary["total_pages"])
                            with col2:
                                st.metric("Compliant", summary["compliant_pages"])
                            with col3:
                                st.metric(
                                    "Non-Compliant", summary["non_compliant_pages"]
                                )

                            # Detailed report for each standard
                            st.subheader("Standard-by-Standard Report")
                            for check_name, check_data in summary["checks"].items():
                                with st.expander(
                                    f"{check_name} - {'✅ Compliant' if check_data['is_overall_compliant'] else '❌ Non-Compliant'}"
                                ):
                                    if check_data["compliant_pages"]:
                                        st.markdown(
                                            f"**Compliant {'Pages' if len(images) > 1 else 'Image'}:** {', '.join(map(str, check_data['compliant_pages']))}"
                                        )

                                    if check_data["non_compliant_pages"]:
                                        st.markdown(
                                            f"**Non-Compliant {'Pages' if len(images) > 1 else 'Image'}:** {', '.join(map(str, check_data['non_compliant_pages']))}"
                                        )

    # Footer
    st.markdown("---")
    st.markdown("FinalCheck - PDF Compliance Verification System")


if __name__ == "__main__":
    main()
