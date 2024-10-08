`manual-classifier` is a simple Python GUI tool for manually classifying text blocks in PDF files. The tool displays each block of text from a PDF, allowing users to classify them as "Header," "Body," "Footer," or "Quote" using buttons or keyboard shortcuts (0-3). Users can undo the last classification. The blocks are then written into an output file in their appropriate tags for further automated processing, for instance with my repository [txt-to-epub](https://github.com/Taylor-eOS/txt-to-epub), which should in theory work.

### How to use:
- Run `manually_classify.py`.
- Enter the PDF file name when prompted.
- Use the GUI to classify each text block.
- The classifications are saved to `output.txt`.

This was originally meant to create training data for an automated classifier, but that was so much trouble that the manual classification seems easier.
