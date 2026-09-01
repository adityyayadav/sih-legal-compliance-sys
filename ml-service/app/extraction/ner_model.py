from typing import List, Dict, Optional

class AddressNERModel:
    def __init__(self, model_path: Optional[str] = None):
        """
        Initializes the NER model. 
        In production, load fine-tuned weights from app/models/ner/ here.
        """
        self.model_path = model_path
        # Fallback keywords for heuristic extraction if weights are missing
        self.address_keywords = ["pvt", "ltd", "mfg", "manufactured by", "marketed by", "estate", "road", "phase"]

    def extract_manufacturer_info(self, ocr_results: List[Dict]) -> Optional[Dict]:
        """
        Scans OCR results to extract the manufacturer name and address block.
        Returns the best matching OCR block based on NER/Heuristics.
        """
        best_candidate = None
        highest_score = 0
        
        for block in ocr_results:
            text = block.get("text", "").lower()
            score = sum(1 for keyword in self.address_keywords if keyword in text)
            
            if score > highest_score:
                highest_score = score
                best_candidate = block
                
        return best_candidate