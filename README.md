<div id="readme-top"></div>

<div align="center">
  <a href="#">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>
  <h3 align="center">QR Code Generator 🌟</h3>
  <p align="center">
    A multi-version, customizable QR code generator with Web demo support.<br />
    <a href="#getting-started"><strong>Quick Start »</strong></a>
    <br /><br />
    <a href="#usage">Usage</a>
    &middot;
    <a href="#contact">Contact Us</a>
  </p>
</div>


****

| Author       | StudentID              | 
|--------------|------------------------|
| Shen Fangjie | 31808395 👨‍💻 |



<details>
  <summary><span style="font-size: 20px; font-weight: bold;">Table of Content 📚</span></summary>
  <ol>
    <li><a href="#about-the-project">About the Project</a></li>
    <li><a href="#getting-started">Quick Start</a></li>
    <li><a href="#usage">Usage Example</a></li>
    <li><a href="#project-architecture">Project Architecture</a></li>
    <li><a href="#programming-paradigms">Programming Paradigms</a></li>
    <li><a href="#compliance">Compliance</a></li>
    <li><a href="#technical-weaknesses">Technical Weaknesses</a></li>
    <li><a href="#information-modeling">Data Modeling & Security</a></li>
    <li><a href="#real-world-functions">Real-World Functions</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>

---

## About The Project

This project is a Python-based QR code generator supporting QR code V1/V2 versions, with rich customization features (color, gradient, border, etc.), and provides a web-based interactive interface. The project adopts a modular design, with a clear code structure for easy maintenance and expansion.

**Main Features:**
- For version 1, uses one masking pattern (pattern 0)
- For version 2, uses 8 masking patterns and 4 penalty scores, and can automatically expand to version 2 if version 1 is insufficient
- Uses byte mode bits
- Correctly uses separators, finder, alignment, timing patterns, dark module, and format information
- Built-in Reed-Solomon error correction at level L
- Supports visual customization such as color, gradient, border, etc.
- Provides Flask web interface
- Shows detailed steps and animation of QR code generation

<p align="right">(<a href="#readme-top">Back to top</a>)</p>

---

## Getting Started

This section will guide you on how to quickly run this project locally.

### Prerequisites

- Python 3.11.7
- It is recommended to use a conda virtual environment

### Installation Steps

1. Clone this repository
   ```sh
   git@csgitlab.reading.ac.uk:python-cw2_group_srt_pyx_mlp_sfj_zez/Python-CW2_Group3.git
   ```
2. Install dependencies
   ```sh
   pip install -r requirements.txt
   ```
3. Run the web interface
   ```sh
   python app.py
   ```

<p align="right">(<a href="#readme-top">Back to top</a>)</p>

---

## Usage (tip: The gif file may take a few seconds to load. Please wait patiently.)

1. After running app.py in your IDE, visit http://localhost:5000 in your browser, **select Version 1, enter "HelloMyFriend", and the generated QR code can be correctly recognized and scanned**
   - **Gif 1: Input Interface**
     ![gif1](images/gif1.GIF)
   - **Screenshot 2: Scan Result**
   
     ![Scan Result](https://csgitlab.reading.ac.uk/python-cw2_group_srt_pyx_mlp_sfj_zez/Python-CW2_Group3/-/raw/main/images/screenshot2.png)

2. **If you enter a URL longer than Version 1's capacity in the Version 1 interface, an error will be prompted**
   - **Gif 3: Error Message**
     ![gif3](images/gif3.GIF)

3. **Next is Project Enhancement, which adds support for Version 2. The version is automatically selected based on the input text length. It also applies 8 mask patterns and 4 penalty scores to automatically select the best mask pattern. Users can also customize QR code background and color rendering**
   - **Gif 4: Enter "HelloMyFriend", use Version 1, and select  blue QR code and red background in the palette**
     ![gif4](images/gif4.GIF)
   - **Gif 5: Enter URL [http://www.baidu.com](http://www.baidu.com), use Version 2**
     ![gif5](images/gif5.GIF)
   - **Screenshot 6: Scan Result**

     ![Scan Result Version 2](https://csgitlab.reading.ac.uk/python-cw2_group_srt_pyx_mlp_sfj_zez/Python-CW2_Group3/-/raw/main/images/screenshot6.png)

4. **Select Show all masks & scores to display the scores of all 8 masks and the best score for this QR code**
   - **Gif 7: Mask Scores**
     ![gif7](images/gif7.GIF)

5. **Select Process, then demonstrate the QR code you want, and you can display the details of our QR code generation step-by-step**
   - **Gif 8.1: QR Code Generation Step 1**
     ![gif8.1](images/gif8.1.GIF)
   - **Gif 8.2: QR Code Generation Step 2**
     ![gif8.2](images/gif8.2.GIF)
   - **Gif 8.3: QR Code Generation Step 3**
     ![gif8.3](images/gif8.3.GIF)
   - **Gif 8.4: QR Code Generation Step 4**
     ![gif8.4](images/gif8.4.GIF)
   - **Gif 8.5: QR Code Generation Step 5**
     ![gif8.5](images/gif8.5.GIF)

6. **Select Source Code to view our information and the project link of the source code**
   - **Gif 9: Source Code Link**
     ![gif9](images/gif9.GIF)
<p align="right">(<a href="#readme-top">Back to top</a>)</p>

---

## Project Architecture

### Basic QR Data Generation
- **Data Encoding**: Implements Byte Mode encoding using 8-bit ASCII. Correctly assembles mode bits, character count bits, and data bits (including terminator and padding) to form codewords from the input string.
- **Error Correction Integration**: Utilizes the `reedsolo` library at ECC Level L. For Version 1, generates 19 data codewords and 7 ECC codewords, totaling 26 codewords in the correct order.
- **Matrix Layout and Patterns**: Constructs a `21×21 matrix` for Version 1 with finder patterns in corners, timing patterns, dark module, and reserved format information areas. Data/ECC bits are placed in a zigzag manner, applying one masking pattern.

### Basic Interactive QR Data Presentation
- **Basic Website Interactivity**: Provides a user-friendly `Flask` web interface allowing users to input text/URL and generate QR codes.
- **Presentation and Visualisation**: QR codes are rendered as images with clear labels and instructions. Interface layout is intuitive and user-friendly.
- **Testing and Demonstration**: Generated QR codes are confirmed scannable using a phone QR app. Includes test QR images in `test_QRcode`.

### Project Enhancements
- **Version 2 and Automatic Version Selection**: Automatically switches to Version 2 (`25×25 matrix`) when input exceeds Version 1 capacity, including alignment patterns.
- **Multiple Mask Patterns and Penalty Scoring**: Implements all eight mask patterns (0–7) and calculates penalty scores to automatically select the best mask. Demonstrates mask evaluation process.
- **Step-by-Step Display**: Offers a user option to display a slideshow showing the QR code construction process (finder patterns, data bits, masking) for educational purposes.

<p align="right">(<a href="#readme-top">Back to top</a>)</p>

---

## Programming Paradigms

- **Imperative**: Matrix construction uses nested loops for step-by-step filling.
- **Functional**: Core algorithms such as encoding conversion are implemented as pure functions for easy testing.
- **Object-Oriented**: The core `QRBuilder` class encapsulates all generation logic for easy extension and maintenance.

<p align="right">(<a href="#readme-top">Back to top</a>)</p>

---

## Compliance

- **Readability**: UI text automatically wraps and centers, warning messages are highlighted.
- **Security**: All user data is processed only in memory, with no persistence or network transmission, complying with GDPR and other privacy regulations.
- **Legal Compliance**: No external data collection, fully local operation.

<p align="right">(<a href="#readme-top">Back to top</a>)</p>

---

## Technical Weaknesses

- Only supports V1/V2 versions, expansion requires refactoring
- Only supports L-level error correction
- Radial gradient is actually linear gradient, needs improvement in the future

<p align="right">(<a href="#readme-top">Back to top</a>)</p>

---

## Data Management and Security

- **Data Modeling**: Strictly follows ISO/IEC 18004 standard, with clear data flow.
- **Input Management**: Frontend validates input to prevent empty or overlong values.
- **Data Security**: All data is processed only in memory and destroyed after generation.

<p align="right">(<a href="#readme-top">Back to top</a>)</p>

---

## Real-World Functions

- **Marketing**: Custom brand color QR codes to enhance brand recognition
- **Inventory Management**: Adjustable size and border to suit different scenarios
- **Product Anti-counterfeiting**: Supports encryption and database linkage for traceability

<p align="right">(<a href="#readme-top">Back to top</a>)</p>

---

## Contributing

PRs and Issues are welcome! Please fork this repository, develop on a branch, and submit a PR.

1. Fork this project: [https://csgitlab.reading.ac.uk/python-cw2_group_srt_pyx_mlp_sfj_zez/Python-CW2_Group3](https://csgitlab.reading.ac.uk/python-cw2_group_srt_pyx_mlp_sfj_zez/Python-CW2_Group3)
2. Create a new branch (`git checkout -b feature/xxx`)
3. Commit your changes (`git commit -m 'Add xxx'`)
4. Push the branch (`git push origin feature/xxx`)
5. Submit a PR

<p align="right">(<a href="#readme-top">Back to top</a>)</p>

---

## License

This project is licensed under the MIT License. See `LICENSE` for details.

<p align="right">(<a href="#readme-top">Back to top</a>)</p>

---

## Contact

Author: Pan Yuxuan, Shen Ruiting, Shen Fangjie, Zhang Enze, Mao Leping

Project address: [GitLab](https://csgitlab.reading.ac.uk/python-cw2_group_srt_pyx_mlp_sfj_zez/Python-CW2_Group3)

<p align="right">(<a href="#readme-top">Back to top</a>)</p>
