from PIL import Image
import sys

def main(path='sample.jpg'):
    img = Image.new('RGB', (320, 240), color=(73, 109, 137))
    img.save(path, 'JPEG')
    print(path)

if __name__ == '__main__':
    p = sys.argv[1] if len(sys.argv) > 1 else 'sample.jpg'
    main(p)
