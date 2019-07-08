mkdir /home/ec2-user/ocr/images/

aws s3 sync s3://ocr-research/ /home/ec2-user/ocr/images/

python /home/ec2-user/ocr/scripts/Final_OCR_v2.py

rm -r /home/ec2-user/ocr/images/

aws s3 rm s3://ocr-research --recursive
