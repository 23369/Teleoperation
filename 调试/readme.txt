Input: adb devices
Output: 2G0YC5ZG7R078C	device
Input: adb -s 2G0YC5ZG7R078C reverse tcp:8012 tcp:8012
Input: sudo adb -s 2G0YC5ZG7R078C reverse --list
Output: UsbFfs tcp:8012 tcp:8012

cd Documents/avp_teleoperate/teleop

python open_television/television.py \
  --Vuer.cert=../cert.pem \
  --Vuer.key=../key.pem \
  --Vuer.port=8012 \
  --Vuer.host=0.0.0.0
  
  
python teleop_hand_and_arm.py --arm=G1_29 --hand=inspire1 --record
