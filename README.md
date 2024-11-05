`manual-classifier` is a simple Python GUI tool for extracting and classifying text blocks from PDF files. The tool displays each block of text, allowing the user to select "Header," "Body," "Footer," or "Quote" using buttons or keyboard shortcuts (1-3, H, E). In the case of a mistake, the last classification can be undone (or the output file edited). The blocks are written into an output file in their appropriate tags for further automated processing, for instance with [txt-to-epub](https://github.com/Taylor-eOS/txt-to-epub).

### How to use:
- Make a project, venv environment, and install requirements. (A detailed guide for the whole installation process can be found [here](https://github.com/Taylor-eOS/whisper).
- Run `python manually_classify.py`.
- Enter input file basename when prompted.
- Use the GUI to classify each text block.
- The classifications are saved to `output.txt`.

This was originally meant to create training data for [a machine learning classifier](https://github.com/Taylor-eOS/bert-classifier). However that proved too unreliable, so the manual classification is preferred.
