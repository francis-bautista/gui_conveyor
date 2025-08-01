
class FormulaController:
    def __init__(self, ripeness, bruises, size):
        self.RIPENESS_SCORES = ripeness
        self.BRUISES_SCORES = bruises
        self.SIZE_SCORES = size

    def get_grade_formula(self, priorities):
        max_score = (priorities['ripeness'] * self.RIPENESS_SCORES['green'] + 
                    priorities['bruises'] * self.BRUISES_SCORES['unbruised'] + 
                    priorities['size'] * self.SIZE_SCORES['large'])
        
        min_score = (priorities['ripeness'] * self.RIPENESS_SCORES['yellow'] + 
                    priorities['bruises'] * self.BRUISES_SCORES['bruised'] + 
                    priorities['size'] * self.SIZE_SCORES['small'])
        
        segment_size = (max_score - min_score) / 3
        
        return {
            'A': {'min': max_score - segment_size, 'max': max_score},
            'B': {'min': max_score - 2 * segment_size, 'max': max_score - segment_size},
            'C': {'min': min_score, 'max': max_score - 2 * segment_size}
        }

    def is_number(self, textbox):
        try:
            value = textbox.get()
            float(value)
            return True
        except ValueError:
            return False

    def is_valid_priority(self, combo_boxes):
        all_valid = True
        all_values = []
        error_type = "null"
        for key, combo in combo_boxes.items():
            value = combo.get()
            if value == "" or value is None:
                error_type = "is_null"
                all_valid = False
                break
            try:
                numeric_value = float(value)
                all_values.append(numeric_value)
            except ValueError:
                error_type = "not_num"
                all_valid = False
                break
        if all_valid:
            if all(v == 0.0 for v in all_values):
                error_type = "all_zero"
                all_valid = False

        return [all_valid, error_type]


    def set_input_priority(self, arr):
        print(arr)
        self.input_priorities = arr

    def get_priorities(self):
        return self.input_priorities

    def get_grade_letter(self, input_grade):
        boundaries = self.get_grade_formula(self.input_priorities)
        self.print_grade_formula(boundaries)
        if boundaries['A']['min'] <= input_grade <= boundaries['A']['max']:
            return "A"
        elif boundaries['B']['min'] <= input_grade < boundaries['B']['max']:
            return "B"
        else:
            return "C"

    def print_grade_formula(self, boundaries):
        print("Calculated Grade Range")
        for grade in ['A', 'B', 'C']:
            min_val = boundaries[grade]['min']
            max_val = boundaries[grade]['max']
            range_size = max_val - min_val
            # print(f"Grade {grade}: {max_val:.2f} - {min_val:.2f}, Range: {range_size:.2f}")

    def get_grade_formula_dict(self):
        boundaries = self.get_grade_formula(self.input_priorities)       
        print("Calculated Grade Range")
        grade_dict = {}
        for grade in ['A', 'B', 'C']:
            min_val = boundaries[grade]['min']
            max_val = boundaries[grade]['max']
            range_size = max_val - min_val
            grade_string = f"{max_val:.2f} - {min_val:.2f}, Range: {range_size:.2f}"
            grade_dict[grade] = grade_string
            # print(f"Grade {grade}: {grade_string}")
        
        return grade_dict
