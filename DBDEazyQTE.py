import keyboard
import pyautogui
import time
import win32gui,win32ui,win32con
import threading
import numpy as np
from PIL import Image
import winsound
import math


imgdir='DBDimg/'
delay_degree = 0
crop_w, crop_h = 200, 200
last_im_a=0
region=[int((2560-crop_w)/2), int((1440-crop_h)/2),
                  crop_w, crop_h]
toggle=True
keyboard_switch=True
frame_rate=60
repair_speed=330
heal_speed=300
wiggle_speed=230
shot_delay= 0.006574
press_and_release_delay= 0.003206
color_sensitive=125
delay_pixel=0
speed_now = repair_speed
hyperfocus=False
red_sensitive=180
focus_level=0


def sleep(t):
    st = time.time()
    while True:
        offset = time.time() - st
        if offset >= t:
            # print(offset)
            break

def sleep_to(time_stamp):
    while True:
        offset = time.time() - time_stamp
        if offset >= 0:
            # print(offset)
            break

def win_screenshot(startw,starth,w,h):
    # bmpfilenamename = "out.bmp" #set this

    hwnd = 0 # window ID, 0 represents current active window
    # hwnd = win32gui.FindWindow(None, windowname)
    wDC = win32gui.GetWindowDC(hwnd)
    dcObj=win32ui.CreateDCFromHandle(wDC)
    cDC=dcObj.CreateCompatibleDC()
    dataBitMap = win32ui.CreateBitmap()
    dataBitMap.CreateCompatibleBitmap(dcObj, w, h)
    cDC.SelectObject(dataBitMap)
    cDC.BitBlt((0,0),(w, h) , dcObj, (startw,starth), win32con.SRCCOPY)
    # dataBitMap.SaveBitmapFile(cDC, bmpfilenamename)
    signedIntsArray = dataBitMap.GetBitmapBits(True)
    img_array = np.frombuffer(signedIntsArray, dtype='uint8')
    # Free Resources
    dcObj.DeleteDC()
    cDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, wDC)
    win32gui.DeleteObject(dataBitMap.GetHandle())
    img_array.shape = (h,w,4)
    img_array=np.delete(img_array,3,2)[...,::-1]
    # Image.fromarray(img_array).show()
    return img_array
    


def find_red(im_array):
    r_i ,r_j= None,None
    shape = im_array.shape
    
    target_points=[]
    for i in range(shape[0]):
        for j in range(shape[1]):
            if im_array[i][j][0] > red_sensitive and im_array[i][j][1] < 20 and im_array[i][j][2] < 20:
                l1,l2=i-shape[0]/2,j-shape[1]/2
                if l1*l1+l2*l2 > shape[0]*shape[0]/4:
                    # print('not in circle:',i,j)
                    continue
                im_array[i][j]=[255,0,0]
                target_points.append((i,j))
    if not target_points:
        return
    # print(target_points)
    r_i,r_j,max_d= find_thickest_point(shape,target_points)
    if max_d < 1:
        return
    # print("red:",r_i, r_j)
    if not r_i or not r_j:
        return
    
    return (r_i, r_j,max_d)

    
# def find_thickest_point(im_array,r_i,r_j,target_points):
#     from line_profiler import LineProfiler
#     lp = LineProfiler()
#     lp_wrapper = lp(find_thickest_point_pre)
#     result=lp_wrapper(im_array,r_i,r_j,target_points)
#     lp.print_stats()
#     return result

def find_thickest_point(shape,target_points):
    # print(shape)
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
                    # print(max_r,max_d,im_array[i+d][j+d],im_array[i-d][j+d],im_array[i+d][j-d],im_array[i-d][j-d])
            else:
                break
    r_i,r_j = max_r[0],max_r[1]
    return (r_i,r_j,max_d)
    
    
def find_square(im_array):
    
    r_i = None
    shape = im_array.shape
    target_points=[]
    global focus_level
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
    
    r_i,r_j,max_d= find_thickest_point(shape,target_points)
    
    # print("white square:",r_i, r_j)
    if not r_i or not r_j:
        return
    # if max_d < 1:
    #     return 
    pre_d=0
    post_d=0
    target = cal_degree(r_i-crop_h/2, r_j-crop_w/2)
    sin=math.sin(2*math.pi*target/360)
    cos=math.cos(2*math.pi*target/360)
    for i in range(max_d,21):
        pre_i=round(r_i-sin*i)
        pre_j=round(r_j-cos*i)
        if list(im_array[pre_i][pre_j]) ==[0, 0, 255]:
            pre_d=i
        else:
            break
    for i in range(max_d,21):
        pre_i=round(r_i+sin*i)
        pre_j=round(r_j+cos*i)
        if list(im_array[pre_i][pre_j]) ==[0, 0, 255]:
            post_d=i
        else:
            break
    print(pre_d,post_d)
    
    if pre_d + post_d < 5:
        print('merciless storm')
        # Image.fromarray(im_array).save(imgdir+'merciless.png')
        to_be_deleted=[]
        for i,j in target_points:
            if abs(i - r_i) <= 20 and abs(j - r_j) <= 20:
                to_be_deleted.append((i,j))
        print('before',target_points)
    
        for i in to_be_deleted:
            target_points.remove(i)
        print('after',target_points)
        if not target_points:
            return
        r2_i,r2_j,max_d= find_thickest_point(shape,target_points)
        if max_d < 3:
            target1= cal_degree(r_i-crop_h/2, r_j-crop_w/2)
            target2= cal_degree(r2_i-crop_h/2, r2_j-crop_w/2)
            print('storm points',r_i,r_j,r2_i,r2_j)
            if target1 < target2:
                pre_white=(r_i,r_j)
                post_white=(r2_i,r2_j)
            else:
                pre_white=(r2_i,r2_j)
                post_white=(r_i,r_j)
            new_white=(round((pre_white[0]+post_white[0])/2),round((pre_white[1]+post_white[1])/2))
            focus_level=0
            return (new_white,pre_white,post_white)
    
    pre_white=(round(r_i-sin*pre_d),round(r_j-cos*pre_d))
    post_white=(round(r_i+sin*post_d),round(r_j+cos*post_d))

    new_white=(round((pre_white[0]+post_white[0])/2),round((pre_white[1]+post_white[1])/2))
    if list(im_array[new_white[0]][new_white[1]]) != [0, 0, 255]:
        print("new white error")
        return
    # 
               
    return (new_white,pre_white,post_white)

def wiggle(t1,deg1,direction,im1):
    speed=wiggle_speed*direction
    target1=270
    target2=90
    delta_deg1=(target1-deg1)%(direction*360)
    delta_deg2=(target2-deg1)%(direction*360)
    predict_time=min(delta_deg1/speed ,delta_deg2/speed)
    print("predict time",predict_time)
    # sleep(0.75)
    # return #debug 
    
    click_time = t1 + predict_time - press_and_release_delay + delay_degree/abs(speed)

    delta_t = click_time-time.time() 
    
    # print('delta_t',delta_t)
    if delta_t < 0 and delta_t > -0.1:
        keyboard.press_and_release('space')
        print('quick space!!', delta_t, '\nspeed:', speed)
        sleep(0.13)
        return 
    try:
        delta_t = click_time-time.time() 
        sleep(delta_t)
        keyboard.press_and_release('space')
        print('space!!', delta_t, '\nspeed:', speed)
        Image.fromarray(im1).save(imgdir+'log.png')
        sleep(0.13)
    except ValueError as e:
        
        # winsound.Beep(230,300)
        print(e,delta_t, deg1, delta_deg1, delta_deg2)

def timer(im1, t1):
    global focus_level
    if not toggle:
        return
    # print('timer',time.time())
    r1 = find_red(im1)
    if not r1:
        return

    deg1 = cal_degree(r1[0]-crop_h/2, r1[1]-crop_w/2)


    
    # print('first seen:',deg1,t1)
    global last_im_a
    
    # sleep(1.5)
    # return #debug 
    im2 = win_screenshot(region[0],region[1],crop_w, crop_h)

    r2 = find_red(im2)
    
    if not r2:
        return 
    
    
    deg2 = cal_degree(r2[0]-crop_h/2, r2[1]-crop_w/2)
    if deg1 == deg2:
        # print("red same")
        return
    # speed = (deg2-deg1)/(t2-t1)
    
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
    
    
    # im2[pre_i][pre_j][0] > 200 and im2[pre_i][pre_j][1] < 20 and im2[pre_i][pre_j][2] < 20:
    

    
    
    
    white = find_square(im1)
    
    
    if not white:
        return
    print(white)
    white,pre_white,post_white=white

    if direction < 0:
        pre_white,post_white=post_white,pre_white
    im1[r1[0]][r1[1]]=[0,255,0]
    im1[white[0]][white[1]]=[0,255,0]
    last_im_a=im1
    
    
    print('targeting_time:',time.time()-t1)
    print('speed:',speed)
    
    
    
    target = cal_degree(white[0]-crop_h/2, white[1]-crop_w/2)
    # target=180
    

    # if target< 45 or target > 315 or (target>135 and target<225):
    #     white_2=(white[0],white[1]-max_d)
    #     white_3=(white[0],white[1]+max_d)
    # else:
    #     white_2=(white[0]-max_d,white[1])
    #     white_3=(white[0]+max_d,white[1])

    delta_deg=(target-deg1)%(direction*360)
    
    print("predict time",delta_deg/speed)
    # sleep(0.75)
    # return #debug 
    
    click_time = t1 + delta_deg/speed -press_and_release_delay + delay_degree/abs(speed)
    # print("minus ",click_time%(1/frame_rate))
    # click_time-=click_time%(1/frame_rate)
    delta_t = click_time-time.time() 
    
    
    # sin=math.sin(2*math.pi*target/360)
    # cos=math.cos(2*math.pi*target/360) 
    max_d=r1[2]
    global delay_pixel
    start_point=post_white
    sin=math.sin(2*math.pi*target/360)
    cos=math.cos(2*math.pi*target/360)
    max_d+=delay_pixel
    delta_i=pre_white[0]-white[0]
    delta_j=pre_white[1]-white[1]
    # if hyperfocus:
    #     delta_i*=(1+0.04*focus_level)
    #     delta_j*=(1+0.04*focus_level)
    end_point=[white[0]+round(delta_i-direction*sin*(-max_d)),white[1]+round(delta_j-direction*cos*(-max_d))]
    check_points=[]
    if abs(end_point[0]-start_point[0]) < abs(end_point[1]-start_point[1]):
        for j in range(start_point[1],end_point[1],2*np.sign(end_point[1]-start_point[1])):
            i=start_point[0]+(end_point[0]-start_point[0])/(end_point[1]-start_point[1])*(j-start_point[1])
            i=round(i)
            check_points.append((i,j))
    elif np.sign(end_point[0]-start_point[0])==0:
        return
    else:
        for i in range(start_point[0],end_point[0],2*np.sign(end_point[0]-start_point[0])):
            j=start_point[1]+(end_point[1]-start_point[1])/(end_point[0]-start_point[0])*(i-start_point[0])
            j=round(j)
            check_points.append((i,j))
    check_points.append(end_point)
    print('check points',check_points)
    pre_4deg_check_points=[]
    
    if abs(end_point[0]-start_point[0])**2 + abs(end_point[1]-start_point[1])**2 < 20**2: 
        start_point=pre_white
        end_point=(end_point[0]+delta_i,end_point[1]+delta_j)
        # if the white area is  too large dont use pre_4deg
        if abs(end_point[0]-start_point[0]) < abs(end_point[1]-start_point[1]):
            for j in range(start_point[1],end_point[1],2*np.sign(end_point[1]-start_point[1])):
                i=start_point[0]+(end_point[0]-start_point[0])/(end_point[1]-start_point[1])*(j-start_point[1])
                i=round(i)
                pre_4deg_check_points.append((i,j))
        elif np.sign(end_point[0]-start_point[0])==0:
            return
        else:
            for i in range(start_point[0],end_point[0],2*np.sign(end_point[0]-start_point[0])):
                j=start_point[1]+(end_point[1]-start_point[1])/(end_point[0]-start_point[0])*(i-start_point[0])
                j=round(j)
                pre_4deg_check_points.append((i,j))
        pre_4deg_check_points.append(end_point)
    else:
        print('[!]large white area detected')
        check_points.pop()

    #TODO: extend pre_4deg_check_points for more degs
    
    print('pre 4 deg check points',pre_4deg_check_points)
    
    print('delta_t',delta_t)
    if delta_t < 0 and delta_t > -0.1:
        keyboard.press_and_release('space')
        print('[!]quick space!!', delta_t, '\nspeed:', speed)
        # sleep(0.5)

        if(hyperfocus):
            print('focus hit:',focus_level)
            focus_level=(focus_level+1)%7
        return 
    try:
        delta_t = click_time-time.time() 
        # sleep(max(0,delta_t-0.1))
            
        ## trying to catch
        checks_after_awake=0
        checkwhen=0
        im_array_pre_backup=None
        while True:
            out=False
            im_array_pre = win_screenshot(region[0],region[1],crop_w, crop_h)
            checks_after_awake+=1
            
            for i,j in check_points:
                if  im_array_pre[i][j][0] > red_sensitive and im_array_pre[i][j][1] < 20 and im_array_pre[i][j][2] < 20:
                    out=True
                    im_array_pre[i][j]=[0,255,255]
                    checkwhen=1
                    break
            if out:
                break  
            
            for k in range(len(pre_4deg_check_points)):
                i,j=pre_4deg_check_points[k]
                if  im_array_pre[i][j][0] > red_sensitive and im_array_pre[i][j][1] < 20 and im_array_pre[i][j][2] < 20:
                    out=True
                    checkwhen=2
                    im_array_pre[i][j]=[255,255,0]
                    t=4/speed_now*(1+k)/len(pre_4deg_check_points)-press_and_release_delay
                    if t > 0:
                        sleep(t)
                    break
            if out:
                break  
            if time.time() > click_time+0.04:
                print('catch time out')
                break
            im_array_pre_backup=im_array_pre
        # if speed < 315:
        if type(im_array_pre_backup)==type(None):
           return
            
        keyboard.press_and_release('space')
        print('checktime',checkwhen)
        if checks_after_awake <=1:
            print('[!]awake quick space!!', delta_t, '\nspeed:', speed)
            file_name='awake'
        else:
            print('space!!', delta_t, '\nspeed:', speed)
            file_name=''
        print(im_array_pre[pre_white[0],pre_white[1]])
        # Image.fromarray(im_array3).show()
        # return
        r3= find_red(im_array_pre)
        shape = im_array_pre_backup.shape
        for i in range(shape[0]):
            for j in range(shape[1]):
                if im_array_pre_backup[i][j][0] > red_sensitive and im_array_pre_backup[i][j][1] < 20 and im_array_pre_backup[i][j][2] < 20:
                    l1,l2=i-shape[0]/2,j-shape[1]/2
                    if l1*l1+l2*l2 > shape[0]*shape[0]/4:
                        # print('not in circle:',i,j)
                        continue
                    im_array_pre[i][j]=[255,0,0]
        
        if not r3:
            return
        
        
        deg3=cal_degree(r3[0]-crop_h/2, r3[1]-crop_w/2)
        real_delta_deg=deg3-target
        
        im_array_pre[r1[0]][r1[1]]=[0,255,0]
        im_array_pre[white[0]][white[1]]=[0,0,255]
        
        im_array_pre[r3[0]][r3[1]]=[255,255,0]
        
        for i,j in check_points:
            im_array_pre[i][j]=[255,255,0]
        for i,j in pre_4deg_check_points:
            im_array_pre[i][j]=[0,255,0]
            
        im_array_pre[post_white[0]][post_white[1]]=[0,255,0]
        im_array_pre[pre_white[0]][pre_white[1]]=[0,255,0]
        if hyperfocus:
            file_name+='log_focus'+str(focus_level)+'_'+str(real_delta_deg)+'_'+str(int(time.time()))
        else:
            file_name+='log_'+str(real_delta_deg)+'_'+str(int(time.time()))
        file_name+='speed_'+str(speed)+'.png'
        file_name=imgdir+file_name
        Image.fromarray(im_array_pre).save(file_name)
        # sleep(0.3)
        if(hyperfocus):
            print('focus hit:',focus_level)
            focus_level=min(6,(focus_level+1))
    except ValueError as e:
        Image.fromarray(im1).save(imgdir+'log.png')
        # winsound.Beep(230,300)
        print(e,delta_t, deg1, deg2, target)

    # TODO: if white in im2



def driver():
    # result = {}
    global crop_w, crop_h
    im = pyautogui.screenshot()
    if im.height == 1600: # 2560*1600
        crop_w, crop_h = 250, 250
    elif im.height == 1080: # 1920*1080
        crop_w, crop_h = 150, 150
    elif im.height == 2160: # 3840*2160
        crop_w, crop_h = 330, 330
    global region
    region = [int((im.width-crop_w)/2), int((im.height-crop_h)/2),
                  crop_w, crop_h]
    try:
        while (True):
            # im = Image.open('img/1.png')
            # print('start',time.time())
            t = time.time()
            im_array = win_screenshot(region[0],region[1],crop_w, crop_h)
            timer(im_array, t)
    except KeyboardInterrupt:
        Image.fromarray(last_im_a).save(imgdir+'last_log.png')
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
    global speed_now,delay_pixel,toggle,focus_level,hyperfocus,keyboard_switch
    
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
    if x.name in 'wasd':    
        focus_level=0
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
        delay_pixel+=2
        print('delay_pixel:',delay_pixel)
    if x.name=='-': 
        winsound.Beep(500,500)
        delay_pixel-=2
        print('delay_pixel:',delay_pixel)

        

def main():
    # cap_test()
    
    import os
    if not os.path.exists(imgdir):
        os.mkdir(imgdir)
    keyboard.on_press(keyboard_callback)
    threading.Thread(target=keyboard.wait)
    print('starting')
    driver()


if __name__ == "__main__":
    main()
    
    
