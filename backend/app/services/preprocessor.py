import cv2
import numpy as np
import os

class ImagePreprocessor:
    @staticmethod
    def read_image(file_path: str) -> np.ndarray:
        """Reads an image from path, supporting unicode characters in path."""
        # Reading via numpy to support non-ASCII paths on Windows
        stream = open(file_path, "rb")
        bytes_data = bytearray(stream.read())
        numpy_array = np.asarray(bytes_data, dtype=np.uint8)
        img = cv2.imdecode(numpy_array, cv2.IMREAD_COLOR)
        stream.close()
        return img

    @staticmethod
    def to_grayscale(image: np.ndarray) -> np.ndarray:
        """Converts image to grayscale."""
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    @staticmethod
    def remove_noise(image: np.ndarray) -> np.ndarray:
        """Applies Gaussian Blur to remove noise."""
        return cv2.GaussianBlur(image, (3, 3), 0)

    @staticmethod
    def threshold(image: np.ndarray) -> np.ndarray:
        """Binarizes image using OTSU or adaptive thresholding."""
        # Using OTSU binarization
        _, thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh

    @staticmethod
    def get_skew_angle(thresh_image: np.ndarray) -> float:
        """Calculates skew angle of the text using contour coordinates."""
        # Invert the image (text needs to be white, background black)
        inverted = cv2.bitwise_not(thresh_image)
        
        # Find all coordinates of non-zero pixels
        pts = np.column_stack(np.where(inverted > 0))
        if len(pts) == 0:
            return 0.0
            
        # Get bounding box of all text pixels
        rect = cv2.minAreaRect(pts)
        angle = rect[-1]
        
        # Adjust angle to be in range [-45, 45]
        # In OpenCV, minAreaRect returns angle between [-90, 0) or [0, 90) depending on version
        if angle < -45:
            angle = -(90 + angle)
        elif angle > 45:
            angle = 90 - angle
            
        return angle

    @staticmethod
    def rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
        """Rotates image by a specific angle around its center."""
        if abs(angle) < 0.5:
            return image # No rotation needed for tiny angles
            
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return rotated

    @classmethod
    def preprocess(cls, input_path: str, output_path: str) -> str:
        """
        Runs the full preprocessing pipeline:
        Grayscale -> Blur -> Threshold -> Deskew -> Save.
        """
        img = cls.read_image(input_path)
        if img is None:
            raise ValueError(f"Could not load image from {input_path}")
            
        gray = cls.to_grayscale(img)
        denoised = cls.remove_noise(gray)
        thresh = cls.threshold(denoised)
        
        # Compute skew angle and deskew
        angle = cls.get_skew_angle(thresh)
        deskewed = cls.rotate_image(img, angle)
        
        # Save the final preprocessed image
        # Using numpy to save supporting non-ASCII paths
        _, ext = os.path.splitext(output_path)
        is_success, buffer = cv2.imencode(ext, deskewed)
        if not is_success:
            raise ValueError(f"Could not encode and save image to {output_path}")
            
        with open(output_path, "wb") as f:
            f.write(buffer)
            
        return output_path
