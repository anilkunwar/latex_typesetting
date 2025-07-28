import streamlit as st
import os
import tempfile
import zipfile
from datetime import datetime
from pylatex import Document, Command
from pylatex.utils import NoEscape
import subprocess

# Streamlit page configuration
st.set_page_config(page_title="Simple LaTeX ZIP Compiler (PyLaTeX)", layout="wide")

# Title and description
st.title("Simple LaTeX ZIP Compiler (PyLaTeX)")
st.write("Upload a ZIP file or specify the name of a ZIP file in the same directory as this script, containing a simple `main.tex`. Compile to generate a PDF using PyLaTeX.")

# Tabs for upload or adjacent ZIP file
tab1, tab2 = st.tabs(["Upload ZIP File", "Use Adjacent ZIP File"])

# Initialize zip_path
zip_path = None
pdf_data = None
pdf_filename = None

with tab1:
    # File uploader for ZIP file
    uploaded_zip = st.file_uploader("Upload ZIP file", type=["zip"], key="uploader")
    if uploaded_zip is not None:
        # Save uploaded ZIP to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_zip:
            tmp_zip.write(uploaded_zip.read())
            zip_path = tmp_zip.name

with tab2:
    # Text input for ZIP file name in the same directory
    zip_filename_input = st.text_input("Enter ZIP file name (e.g., simple_test.zip)", key="zip_filename")
    if zip_filename_input:
        # Get the directory of the current .py file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        local_zip_path = os.path.join(script_dir, zip_filename_input)
        if os.path.exists(local_zip_path) and zip_filename_input.endswith(".zip"):
            zip_path = local_zip_path
        else:
            st.error(f"ZIP file '{zip_filename_input}' not found in the same directory as the script or is not a valid ZIP file.")

# Compile button and processing logic
if zip_path is not None and st.button("Compile LaTeX"):
    try:
        # Create a temporary directory to store extracted files
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Extract the ZIP file
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(tmpdirname)

            # Log extracted files for debugging
            extracted_files = []
            for root, _, files in os.walk(tmpdirname):
                for file in files:
                    extracted_files.append(os.path.join(root, file))
            if extracted_files:
                st.write("Extracted files:", extracted_files)
            else:
                st.error("No files found in the ZIP. Please ensure the ZIP contains files.")

            # Search for main.tex recursively
            tex_file_path = None
            for root, _, files in os.walk(tmpdirname):
                if "main.tex" in files:
                    tex_file_path = os.path.join(root, "main.tex")
                    break
            if not tex_file_path:
                st.error("`main.tex` not found in the ZIP file. Please include a `main.tex` file.")
            else:
                # Read main.tex content for debugging
                with open(tex_file_path, "r", encoding="utf-8") as f:
                    tex_content = f.read()
                st.write("Content of main.tex:", tex_content)

                # Compile with PyLaTeX
                try:
                    # Create a PyLaTeX document
                    doc = Document(documentclass=Command('documentclass', arguments=['article']))
                    doc.append(NoEscape(tex_content))  # Append raw main.tex content

                    # Compile to PDF with pdflatex and capture output
                    pdf_path = os.path.join(tmpdirname, "main")
                    try:
                        process = subprocess.run(
                            ['pdflatex', '--interaction=nonstopmode', f'-output-directory={tmpdirname}', tex_file_path],
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        pdf_file_path = pdf_path + ".pdf"
                        if process.returncode == 0 and os.path.exists(pdf_file_path):
                            # Read the PDF file
                            with open(pdf_file_path, "rb") as f:
                                pdf_data = f.read()
                            pdf_filename = f"compiled_main_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

                            # Display success message
                            st.success("LaTeX compiled successfully with PyLaTeX!")

                            # Provide download button for the PDF
                            st.download_button(
                                label="Download PDF",
                                data=pdf_data,
                                file_name=pdf_filename,
                                mime="application/pdf"
                            )

                            # Embed PDF for preview
                            st.write("### PDF Preview")
                            st.components.v1.html(
                                f"""
                                <object data="data:application/pdf;base64,{pdf_data.hex()}" type="application/pdf" width="100%" height="600px">
                                    <p>Your browser does not support PDF preview. Please download the PDF.</p>
                                </object>
                                """,
                                height=600
                            )
                        else:
                            st.error("PDF generation failed. Check the pdflatex log below:")
                            st.text_area("pdflatex Log", value=process.stdout + process.stderr, height=200, disabled=True)

                    except subprocess.TimeoutExpired:
                        st.error("LaTeX compilation timed out. Please simplify your document or check for errors.")
                    except Exception as pdflatex_error:
                        st.error(f"pdflatex compilation failed: {str(pdflatex_error)}")
                        st.write("Please ensure `main.tex` is a simple LaTeX file without complex dependencies.")

                except Exception as pylatex_error:
                    st.error(f"PyLaTeX setup failed: {str(pylatex_error)}")
                    st.write("Please ensure `main.tex` is a simple LaTeX file without complex dependencies.")

    except zipfile.BadZipFile:
        st.error("Invalid ZIP file. Please upload or specify a valid ZIP archive.")
    except PermissionError:
        st.error("Permission denied while accessing ZIP file or extracted files. Check file permissions.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
    finally:
        # Clean up temporary uploaded ZIP file if it exists
        if uploaded_zip is not None and zip_path is not None and os.path.exists(zip_path):
            os.unlink(zip_path)

# Instructions for the user
st.markdown("""
### Instructions
1. **Upload Option**: Use the "Upload ZIP File" tab to upload a ZIP containing a simple `main.tex`.
2. **Adjacent ZIP Option**: Use the "Use Adjacent ZIP File" tab to enter the name of a ZIP file (e.g., `simple_test.zip`) located in the same directory as this script.
3. Ensure `main.tex` is included in the ZIP (can be in a subdirectory) and is a simple LaTeX file without complex dependencies (e.g., custom .sty or .bib files).
4. Click the "Compile LaTeX" button to generate the PDF using PyLaTeX.
5. Download the PDF or view it in the preview section.
6. Install required dependencies:
   - `pip install streamlit pylatex`
   - `sudo apt-get install texlive` (minimal LaTeX distribution for pdflatex).
7. Example `main.tex`:
   ```latex
   \\documentclass[a4paper,12pt]{article}
   \\usepackage[utf8]{inputenc}
   \\usepackage[T1]{fontenc}
   \\begin{document}
   \\title{Simple Test Document}
   \\author{Test Author}
   \\date{\\today}
   \\maketitle
   \\section{Introduction}
   This is a simple LaTeX document for testing.
   \\end{document}
   ```
8. Create a ZIP with `main.tex` (e.g., `zip -r simple_test.zip simple_test/` after placing `main.tex` in `simple_test/`).
""")
