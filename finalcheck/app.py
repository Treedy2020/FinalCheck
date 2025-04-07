import os
import tempfile

import pymupdf
import streamlit as st
from PIL import Image

from finalcheck.utils import (
    CHECK_CRITERIA,
    NAME_MAP,
    analyze_page_with_vision_api,
    generate_summary_report,
)

os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
os.environ["OPENAI_BASE_URL"] = st.secrets["OPENAI_BASE_URL"]


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
    """Process single image file and return as PIL Image
    
    Args:
        image_file: The uploaded image file object
        
    Returns:
        PIL.Image: The processed image
    """
    return Image.open(image_file)


def main():
    """Main function to run the inspection application"""
    # App configuration
    st.set_page_config(
        page_title="Inspection before Production",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("Inspection before Production")

    st.subheader("Upload File")
    file_type = st.radio(
        "Select file type to upload:",
        ["PDF", "Image"],
        help="Choose whether to upload a PDF document or a single image file",
    )

    if file_type == "PDF":
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
    active_checks = st.multiselect(
        "Select compliance checks:",
        list(CHECK_CRITERIA.keys()),
        default=list(CHECK_CRITERIA.keys()),
    )
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
                        if file_type == "PDF":
                            images = process_pdf(uploaded_file)
                            st.success(
                                f"✅ Successfully extracted {len(images)} pages from the PDF."
                            )
                        else:
                            images = [process_image(uploaded_file)]
                            st.success("✅ Successfully uploaded the image for processing, please wait for the analysis.")

                        tab1, tab2 = st.tabs(
                            ["Analysis", "Compliance Report"]
                        )


                        with tab1:
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
                                            if (standard_name := check_result.get("standard_name", "Unknown Standard")) in NAME_MAP:
                                                standard_name_ = NAME_MAP[standard_name]
                                                st.markdown(
                                                    f"""### {standard_name_}
                                                    Criteria: {CHECK_CRITERIA[standard_name_]['description']}
                                                    """
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
                                                st.error("No analysis results available, this is not desired, please contact the developer.")
                                    else:
                                        st.error("No analysis results available.")

                        with tab2:
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
    st.markdown("Final Inspection before Production, demo provided by **Richard Cui**.")


if __name__ == "__main__":
    main()
