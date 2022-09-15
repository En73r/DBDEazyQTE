import keyboard,pyautogui,winsound
import os,math,time
import win32gui,win32ui,win32con
import threading
import numpy as np
from PIL import Image

imgdir='DBDimg/'
delay_degree = 0
crop_w, crop_h = 200, 200
last_im_a=0
region=[int((2560-crop_w)/2), int((1440-crop_h)/2),
                  crop_w, crop_h]
toggle=True
keyboard_switch=True
repair_speed=330
heal_speed=300
wiggle_speed=230
shot_delay= 0.006574
press_and_release_delay= 0.003206
color_sensitive=125
sensitive_offset=0
speed_now = repair_speed
hyperfocus=False
focus_level=0

def win_screenshot(startw,starth,w,h):
    hwnd = 0 
    wDC = win32gui.GetWindowDC(hwnd)
    dcObj=win32ui.CreateDCFromHandle(wDC)
    cDC=dcObj.CreateCompatibleDC()
    dataBitMap = win32ui.CreateBitmap()
    dataBitMap.CreateCompatibleBitmap(dcObj, w, h)
    cDC.SelectObject(dataBitMap)
    cDC.BitBlt((0,0),(w, h) , dcObj, (startw,starth), win32con.SRCCOPY)
    signedIntsArray = dataBitMap.GetBitmapBits(True)
    img_array = np.frombuffer(signedIntsArray, dtype='uint8')
    dcObj.DeleteDC()
    cDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, wDC)
    win32gui.DeleteObject(dataBitMap.GetHandle())
    img_array.shape = (h,w,4)
    img_array=np.delete(img_array,3,2)[...,::-1]
    return img_array
    


def find_red(im_array):
    r_i ,r_j= None,None
    shape = im_array.shape
    
    target_points=[]
    for i in range(shape[0]):
        for j in range(shape[1]):
            if im_array[i][j][0] > 200 and im_array[i][j][1] < 20 and im_array[i][j][2] < 20:
                l1,l2=i-shape[0]/2,j-shape[1]/2
                if l1*l1+l2*l2 > shape[0]*shape[0]/4:
                    continue
                im_array[i][j]=[255,0,0]
                target_points.append((i,j))
    if not target_points:
        return
    r_i,r_j,max_d= find_thickest_point(im_array,target_points)
    if max_d < 1 or not r_i or not r_j:
        return
    
    return (r_i, r_j)


def find_thickest_point(im_array,target_points):
    shape=im_array.shape
    target_map = np.zeros((shape[0], shape[1]), dtype=bool)
    for i,j in target_points:
        target_map[i][j]=True

    max_r=target_points[0]
    max_d=0

    for i,j in target_points:
        for d in range(1,20):
            if i+d >=shape[0] or j+d >= shape[1] or j-d <0 or i-d < 0:
                break
            elif target_map[i+d][j+d] and target_map[i-d][j-d] and target_map[i-d][j+d] and target_map[i+d][j-d]:
                if d>max_d:
                    max_d=d
                    max_r=[i,j]
            else:
                break
    r_i,r_j = max_r[0],max_r[1]
    return (r_i,r_j,max_d)
    
    
def find_square(im_array):
    r_i = None
    shape = im_array.shape
    target_points=[]
    for i in range(shape[0]):
        for j in range(shape[1]):
            if list(im_array[i][j]) == [255, 255, 255]:
                if i > shape[0]*(200-40)/2/200 and i < shape[0]*(200+40)/2/200 and j > shape[1]*(200-140)/2/200 and j < shape[1]*(200+140)/2/200:
                    im_array[i][j]=[0, 0, 0]
                    continue
                target_points.append((i,j))
                im_array[i][j]=[0, 0, 255]

    if not target_points:
        return
    
    r_i,r_j,max_d= find_thickest_point(im_array,target_points)
    
    if not r_i or not r_j:
        return
    if max_d < 1:
        return 
    pre_d=0
    post_d=0
    target = cal_degree(r_i-crop_h/2, r_j-crop_w/2)
    sin=math.sin(2*math.pi*target/360)
    cos=math.cos(2*math.pi*target/360)
    for i in range(max_d,21):
        pre_i=int(r_i-sin*i)
        pre_j=int(r_j-cos*i)
        if list(im_array[pre_i][pre_j]) ==[0, 0, 255]:
            pre_d=i
        else:
            break
    for i in range(max_d,21):
        pre_i=int(r_i+sin*i)
        pre_j=int(r_j+cos*i)
        if list(im_array[pre_i][pre_j]) ==[0, 0, 255]:
            post_d=i
        else:
            break
    pre_white=(int(r_i-sin*pre_d),int(r_j-cos*pre_d))
    post_white=(int(r_i+sin*post_d),int(r_j+cos*post_d))
    
    new_white=(int((pre_white[0]+post_white[0])/2),int((pre_white[1]+post_white[1])/2))
    if list(im_array[new_white[0]][new_white[1]]) != [0, 0, 255]:
        print("new white error")
        return
               
    return (new_white,pre_white,post_white)

def wiggle(t1,deg1,direction,im1):
    speed=wiggle_speed*direction
    target1=270
    target2=90
    delta_deg1=(target1-deg1)%(direction*360)
    delta_deg2=(target2-deg1)%(direction*360)
    predict_time=min(delta_deg1/speed ,delta_deg2/speed)
    print("predict time",predict_time)

    click_time = t1 + predict_time- press_and_release_delay + delay_degree/abs(speed)

    delta_t = click_time-time.time() 
    
    if delta_t < 0 and delta_t > -0.1:
        keyboard.press_and_release('space')
        print('quick space!!', delta_t, '\nspeed:', speed)
        time.sleep(0.13)
        return 
    try:
        delta_t = click_time-time.time() 
        time.sleep(delta_t)
        keyboard.press_and_release('space')
        print('space!!', delta_t, '\nspeed:', speed)
        # Image.fromarray(im1).save(imgdir+'log.png')
        time.sleep(0.13)
    except ValueError as e:
        
        print(e,delta_t, deg1, delta_deg1, delta_deg2)

def timer(im1, t1):
    global focus_level
    if not toggle:
        return
    r1 = find_red(im1)
    if not r1:
        return

    deg1 = cal_degree(r1[0]-crop_h/2, r1[1]-crop_w/2)
    
    global last_im_a

    im2 = win_screenshot(region[0],region[1],crop_w, crop_h)

    r2 = find_red(im2)
    
    if not r2:
        return
    
    deg2 = cal_degree(r2[0]-crop_h/2, r2[1]-crop_w/2)
    if deg1 == deg2:
        return
    
    if (deg2-deg1)%360 > 180:
        direction=-1
    else:
        direction=1
    
    if speed_now==wiggle_speed:
        print("wiggle")
        return wiggle(t1,deg1,direction,im1)
    if(hyperfocus):
        speed = direction*speed_now*(1+0.04*focus_level)
    else:
        speed = direction*speed_now
    
    
    
    white = find_square(im1)
    
    
    if not white:
        return
    print(white)
    white,pre_white,post_white=white
    
    im1[r1[0]][r1[1]]=[0,255,0]
    im1[white[0]][white[1]]=[0,255,0]
    last_im_a=im1
    
    print('targeting_time:',time.time()-t1)
    print('speed:',speed)
    
    target = cal_degree(white[0]-crop_h/2, white[1]-crop_w/2)
    delta_deg=(target-deg1)%(direction*360)
    print("predict time",delta_deg/speed)
    
    click_time = t1 + delta_deg/speed -press_and_release_delay + delay_degree/abs(speed)
    delta_t = click_time-time.time() 
    print('delta_t',delta_t)
    
    if delta_t < 0 and delta_t > -0.1:
        keyboard.press_and_release('space')
        print('[!]quick space!!', delta_t, '\nspeed:', speed)
        time.sleep(0.7)
        if(hyperfocus):
            print('focus hit:',focus_level)
            focus_level=(focus_level+1)%7
        return 
    try:
        delta_t = click_time-time.time() 
        time.sleep(max(0,delta_t-0.1))
            
        checks_after_awake=0
        while True:
            out=False
            im_array_pre = win_screenshot(region[0],region[1],crop_w, crop_h)
            checks_after_awake+=1
            if  im_array_pre[pre_white[0],pre_white[1]][1] < color_sensitive + sensitive_offset or im_array_pre[white[0],white[1]][1] < color_sensitive + sensitive_offset or  im_array_pre[post_white[0],post_white[1]][1] < color_sensitive + sensitive_offset :
                out=True
                break
            if out:
                break
            if time.time() > click_time+0.04:
                print('catch time out')
                break
            
        keyboard.press_and_release('space')

        print(im_array_pre[pre_white[0],pre_white[1]])

        time.sleep(0.5)
        if(hyperfocus):
            print('focus hit:',focus_level)
            focus_level=min(6,(focus_level+1))
    except ValueError as e:
        # Image.fromarray(im1).save(imgdir+'log.png')
        print(e,delta_t, deg1, deg2, target)




def driver():

    global crop_w, crop_h
    im = pyautogui.screenshot()
    if (im.height == 1600):
        crop_w, crop_h = 250, 250
    elif (im.height == 1080):
        crop_w, crop_h = 150, 150
    global region
    region = [int((im.width-crop_w)/2), int((im.height-crop_h)/2),
                  crop_w, crop_h]

    while (True):
        t = time.time()
        im_array = win_screenshot(region[0],region[1],crop_w, crop_h)
        timer(im_array, t)

def cal_degree(x, y):
    a = np.array([-1, 0])
    b = np.array([x, y])
    a_norm = np.linalg.norm(a)
    b_norm = np.linalg.norm(b)
    a_dot_b = a.dot(b)
    cos_theta = np.arccos(a_dot_b/(a_norm*b_norm))
    degree = np.rad2deg(cos_theta)
    if b[1] < 0:
        degree = 360-degree
    return degree



def keyboard_callback(x):
    global speed_now,sensitive_offset,toggle,focus_level,hyperfocus,keyboard_switch
    
    if x.name=='f1':
        if keyboard_switch:
            winsound.Beep(200,500)
            keyboard_switch=False
            toggle=False
            print('keyboard_switch:', keyboard_switch)
        else:
            winsound.Beep(350,500)
            keyboard_switch=True
            toggle=True
            print('keyboard_switch:', keyboard_switch)
    if not keyboard_switch: 
        return
    if x.name=='caps lock':
        if toggle:
            winsound.Beep(200,500)
            toggle=False
            print('toggle:', toggle)
        else:
            winsound.Beep(350,500)
            toggle=True
            print('toggle:', toggle)
    if not toggle: 
        return
    if x.name=='3':
        toggle=True
        focus_level=0
        print('change to repair')
        winsound.Beep(262,500)
        speed_now=repair_speed
    if x.name=='4':
        toggle=True
        focus_level=0
        winsound.Beep(300,500)
        print('change to heal')
        speed_now=heal_speed
    if x.name=='5':
        toggle=True
        winsound.Beep(440,500)
        print('change to wiggle')
        speed_now=wiggle_speed
    if x.name=='6':
        if hyperfocus:
            winsound.Beep(200,500)
            hyperfocus=False
            print('hyperfocus disabled')
        else:
            winsound.Beep(350,500)
            hyperfocus=True
            print('hyperfocus enabled')
    if x.name=='=':
        winsound.Beep(460,500)
        sensitive_offset+=10
        print('sensitive_offset:',sensitive_offset)
    if x.name=='-': 
        winsound.Beep(500,500)
        sensitive_offset-=10
        print('sensitive_offset:',sensitive_offset)
        

def main():
    if not os.path.exists(imgdir):
        os.mkdir(imgdir)
    keyboard.on_press(keyboard_callback)
    threading.Thread(target=keyboard.wait)
    print('starting')
    driver()


if __name__ == "__main__":
    main()
    
    
