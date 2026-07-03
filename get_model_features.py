
#!/usr/bin/env python3
import pickle
import sys
import os

def get_features_from_model(model_path):
    try:
        with open(model_path, 'rb') as f:
            bundle = pickle.load(f)
            if 'features' in bundle:
                return bundle['features']
            else:
                print(f"Error: 'features' key not found in model bundle at {model_path}")
                return None
    except Exception as e:
        print(f"Error loading model {model_path}: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 get_model_features.py <model_path>")
        sys.exit(1)

    model_path = sys.argv[1]
    features = get_features_from_model(model_path)
    if features:
        for feature in features:
            print(feature)
