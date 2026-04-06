import os
import qrcode


users_file = 'users.txt'
output_dir = 'qrcodes'

os.makedirs(output_dir, exist_ok=True)

with open(users_file, 'r') as file:
    for line in file:
        user_info = line.strip().split(',')
        
  
        if len(user_info) != 3:
            print(f"Skipping invalid line: {line}")
            continue

        user_id, user_name, user_class = user_info

        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(user_id)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img_path = os.path.join(output_dir, f"{user_id}.png")
        img.save(img_path)

        print(f"Generated QR code for {user_name} ({user_id}) in {img_path}")
