from collections import namedtuple
import os
from cv2 import dft
import pandas as pd
from PIL import Image, ImageDraw

import pytesseract
import draw_box as db
from tkinter import Tk
from matplotlib import pyplot as plt
import numpy as np
from io import BytesIO 

pytesseract.pytesseract.tesseract_cmd = r'/usr/local/Cellar/tesseract/5.0.1/bin/tesseract'
#pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
def vscode_find_aoi(image, left, top, right, bottom, level="sub-line", margin_height=4, margin_width=13, AI_suggestions=False):
    """Find Area of Interest in the given image and store the aoi attributes in a Pandas Dataframe
    Parameters
    ----------
    image : str
        filename for the image, e.g. "002-AI-261997-2648858.jpg"
    left : int
        left coordinate of the AOI
    top : int
        top coordinate of the AOI
    right : int
        right coordinate of the AOI
    bottom : int
        bottom coordinate of the AOI
    level : str, optional
        level of detection in AOIs, "line" for each line as an AOI or "sub-line" for each token as an AOI
    margin_height : int, optional
        marginal height when finding AOIs, use smaller number for tight text layout
    margin_width : int, optional
        marginal width when finding AOIs, use smaller number for tight text layout
    AI_suggestions : boolean, optional
        whether AOI include AI suggestions 
    Returns
    -------
    pandas.DataFrame
        a pandas DataFrame of area of interest detected by the method
    """

    #image = os.path.normpath(os.getcwd() + os.sep + os.pardir) + "/Data/" + image

    AI_left, AI_top, AI_right, AI_bottom = 0, 0, 0, 0

    if AI_suggestions == True:
        root = Tk()
        app = db.DrawBox(root, image)
        root.mainloop()
        AI_left, AI_top, AI_right, AI_bottom = app.left, app.top, app.right, app.bottom
    
    img = Image.open(image).convert('L')

    # Go through all the pixels in the image
    for y_pix in range(top, bottom):
        for x_pix in range(left, right):
            # if not 40 <= img.getpixel((x_pix, y_pix)) <= 45:
            #     print(x_pix, y_pix, img.getpixel((x_pix, y_pix)))
            if AI_top < y_pix < AI_bottom and AI_left < x_pix < AI_right:
                if img.getpixel((x_pix, y_pix)) > 80:
                    img.putpixel((x_pix, y_pix), 255)
                
                else:
                    img.putpixel((x_pix, y_pix), 0)
            
            else:
                #convert to white
                if img.getpixel((x_pix, y_pix)) > 80:
                #if img.getpixel((x_pix, y_pix)) > 123:
                    img.putpixel((x_pix, y_pix), 255)

                #convert to black
                else:
                    img.putpixel((x_pix, y_pix), 0)

    cropped = img.crop((left, top, right, bottom))

    size = (1910, 1080)
    layer = Image.new('L', size, 0)
    layer.paste(cropped, tuple((left, top)))
    img = layer

    bottom = bottom + 5
    top = top - 5

    vertical_line = True
    loop_count = 0
    while vertical_line:      
        # Lists for storing results
        vertical_result, upper_bounds, lower_bounds = [], [], []


        # Move the detecting rectangle from the top to the bottom of the image
        for upper in range(top, bottom - margin_height):

            lower = upper + margin_height

            box = (left, upper, right, lower)

            # print(box)
            minimum, maximum = img.crop(box).getextrema()

            if upper > top + 1:
            #if upper > 1:
                if vertical_result[-1][3] == 0 and maximum == 255:
                    # Rectangle detects white color for the first time in a while -> Start of one line
                    upper_bounds.append(upper)
                if vertical_result[-1][3] == 255 and maximum == 0:
                    # Rectangle detects black color for the first time in a while -> End of one line
                    lower_bounds.append(lower)


            # Storing all detection result
            vertical_result.append([upper, lower, minimum, maximum])
        
        final_result = []
        line_count = 1

        left = left - 5
        right = right + 5

        #print(upper_bounds, lower_bounds)

        # Iterate through each line of code from detection
        for upper_bound, lower_bound in list(zip(upper_bounds, lower_bounds)):

            # Reset all temporary result for the next line
            horizontal_result, left_bounds, right_bounds = [], [], []

            # Move the detecting rectangle from the left to the right of the image
            for box_left in range(right - margin_width):

                box_right = box_left + margin_width

                box = (box_left, upper_bound, box_right, lower_bound)

                minimum, maximum = img.crop(box).getextrema()

                if box_left > 1:
                    if horizontal_result[-1][3] == 0 and maximum == 255:
                        # Rectangle detects black color for the first time in a while -> Start of one word
                        left_bounds.append(box_left)
                    if horizontal_result[-1][3] == 255 and maximum == 0:
                        # Rectangle detects white color for the first time in a while -> End of one word
                        right_bounds.append(box_right)

                # Storing all detection result
                horizontal_result.append([box_left, box_right, minimum, maximum])
            
            if level == 'sub-line':

                part_count = 1

                for box_left, box_right in list(zip(left_bounds, right_bounds)):
                    final_result.append(
                        ['sub-line', f'line {line_count} part {part_count}', box_left, upper_bound, box_right, lower_bound])
                    part_count += 1

            elif level == 'line':
                final_result.append(
                    ['line', f'line {line_count}', left_bounds[0], upper_bound, right_bounds[-1], lower_bound])

            line_count += 1
        
        #check if there is a narrow AOI with height of more than 50 pixels
        count = 0
        found = False
        for entry in final_result:
            kind, name, x, y, x0, y0 = entry
            width = x0 - x
            x += margin_width / 2
            width -= margin_width
            height = y0 - y
            if width < 20 and height > 30:
                found = True
                for y_pix in range(y, y0):
                    for x_pix in range(int(x), x0):
                        img.putpixel((x_pix, y_pix), 0)
            if height > 30 and name[-1] == '1':
                for x_pix in range(int(x), x0):
                    pix_count = 0
                    pix = []
                    for y_pix in range(y, y0):
                        if pix_count == 0:
                                pix.append([])
                        if img.getpixel((x_pix, y_pix)) == 255:
                            pix_count += 1
                            pix[-1].append(y_pix)
                        else:
                            if pix_count < 30 and len(pix) > 0:
                                pix.pop(-1)
                            pix_count = 0
                    if len(pix) > 0:
                        found = True
                        for y_pix in pix[0]:
                            img.putpixel((x_pix, y_pix), 0)
            count += 1
            if count == len(final_result) and found == False:
                vertical_line = False
        #if there is no token, then just end the loop
        if len(final_result) == 0:
            vertical_line = False

    #img.show()

    # Format pandas dataframe
    columns = ['kind', 'name', 'aoi_x', 'aoi_y', 'aoi_width', 'aoi_height', 'image']
    aoi = pd.DataFrame(columns=columns)

    for entry in final_result:
        kind, name, x, y, x0, y0 = entry
        width = x0 - x
        height = y0 - y
        image = image

        # For better visualization
        x += margin_width / 2
        width -= margin_width

        value = [kind, name, x, y, width, height, image]
        dic = dict(zip(columns, value))
        df = pd.DataFrame([[kind,name,x, y, width, height, image]], columns=columns)
        # print(dic)
        #df = pd.DataFrame.from_dict(dic, columns = columns)
        # aoi = pd.concat(aoi,df)
        #aoi = aoi.append(dic, ignore_index=True)
        aoi = pd.concat([aoi, df], ignore_index=True)

    return aoi

def check_AI_suggestions(fixated_df):
    AI_suggestions = []

    print(len(fixated_df.index))
    # for each fixation
    for index, row in fixated_df.iterrows():
        img = Image.open(row["image"]).convert('L')
        box_left = int(row["aoi_x"])
        box_top = int(row["aoi_y"])
        box_right = int(box_left + row["aoi_width"])
        box_bottom = int(box_top + row["aoi_height"])
        box = (box_left, box_top, box_right, box_bottom)
        minimum, maximum = img.crop(box).getextrema()
        if maximum < 130:
            AI_suggestions.append(True)
        else:
            AI_suggestions.append(False)
    AI_column = pd.DataFrame(AI_suggestions, columns=['AI_suggestion'])
    fixated_df = pd.concat([fixated_df, AI_column], axis = 1)
    return fixated_df

def vscode_draw_aoi(aoi, image, image_path):
    """Draws AOI rectangles on to an image.
    Parameters
    ----------
    aoi : pandas.DataFrame
        a pandas DataFrame containing rectangle attributes representing areas of interest (AOIs)
    image : str
        filename for the image where AOI rectangles will be imposed, e.g. "vehicle_java.jpg"
    image_path : str
        path for all images, e.g. "emip_dataset/stimuli/"
    Returns
    -------
    PIL.Image
        a PIL image where AOIs have been drawn as rectangles
    """

    # open image
    #img = Image.open(image_path + image)
    img = Image.open(image)

    # draw over image
    draw = ImageDraw.Draw(img)

    # loop over rectangles and draw them
    for row in aoi.iterrows():
        x_coordinate = row[1]['aoi_x']
        y_coordinate = row[1]['aoi_y']
        height = row[1]['aoi_height']
        width = row[1]['aoi_width']
        draw.rectangle([(x_coordinate, y_coordinate),
                        (x_coordinate + width - 1, y_coordinate + height - 1)],
                       outline='#ffffff')

    return img

def crop_image(image, left, top, right, bottom):
    """Crops an image with a given left, top, right, bottom corners
    Parameters
    ----------
    image : str
        filename for the image to be cropped, e.g. "002-AI-261997-2648858.jpg"
    left : int
        left coordinate of the rectangle to be cropped
    top : int
        top coordinate of the rectangle to be cropped
    right : int
        right coordinate of the rectangle to be cropped
    bottom : int
        bottom coordinate of the rectangle to be cropped
    Returns
    -------
    PIL.Image
        a cropped PIL image with the given coordinates
    """
    image = Image.open(os.path.normpath(os.getcwd() + os.sep + os.pardir) + "/Data/" + image).convert('L')
    cropped_image = image.crop((left, top, right, bottom))

    return cropped_image

def image_to_text(img, left, top, right, bottom):
    """Converts an image to text
    Parameters
    ----------
    img : PIL.Image
        a PIL image to be converted to text
    left : int
        left coordinate of the rectangle to be cropped
    top : int
        top coordinate of the rectangle to be cropped
    right : int
        right coordinate of the rectangle to be cropped
    bottom : int
        bottom coordinate of the rectangle to be cropped
    Returns
    -------
    list of str
        a list of strings representing the text in the image
    """
    
    # Opens a image in RGB mode
    #img = Image.open(os.getcwd()+'\\' + image)
    img = crop_image(img, left, top, right, bottom)
    #img.show()

    text = pytesseract.image_to_string(img)
    # text = text.split("\n")
    # print(text)
    # text = [line for line in text if line != '']
    # print(text)
    return text

def add_tokens(aois_raw, aoi_lines):
    """Adds tokens to aois dataframe and returns it.
    Parameters
    ----------
    aois_raw : pandas.Dataframe
        the dataframe where AOIs are stored.
    aoi_lines : list of str
        a list of strings representing the text in the image
    Returns
    -------
    pandas.DataFrame
        a dataframe of AOIs with token information
    """

    filtered_lines = []

    for line in aoi_lines:
        filtered_lines.append(line.split(' '))
    
    # after the code file has been tokenized and indexed
    # we can attach tokens to correct AOI
    aois_raw = aois_raw[aois_raw.kind == "sub-line"].copy()

    tokens = []

    for location in aois_raw["name"].iteritems():
        line_part = location[1].split(' ')
        line_num = int(line_part[1])
        part_num = int(line_part[3])

        if len(filtered_lines) < line_num  or len(filtered_lines[line_num - 1]) < part_num:
            tokens.append("?")
            continue
        tokens.append(filtered_lines[line_num - 1][part_num - 1])

    aois_raw["token"] = tokens

    if aois_raw[aois_raw['token'] == '']['name'].count() != 0:
        print("Error in adding tokens, some tokens are missing!")

    aois_raw.to_csv(os.getcwd()+'/002-Driver-2047253-3277053.jpgaoi_add_token3.csv')
    return aois_raw

def gather_fixations(df):
    """Gathers fixations from a dataframe.
    Parameters
    ----------
    df : pandas.DataFrame
        a dataframe of eye movements
    Returns
    -------
    python list
        a list of fixations including x_cord, y_cord and duration
    """
    fixations = []
    for index, row in df.iterrows():
        if row['eye_event'] == "fixation":
            fixations.append([row['x_cord'], row['y_cord'], row['duration']])

    return fixations

def fixation_offset(x_offset, y_offset, fixation_list):
    """Adds offset to fixations.
    Parameters
    ----------
    x_offset : int
        x offset
    y_offset : int
        y offset
    fixation_list : python list
        a list of fixations including x_cord, y_cord and duration"""

    for index in range(len(fixation_list)):

        fixation_list[index][0] = fixation_list[index][0] + x_offset
        fixation_list[index][1] = fixation_list[index][1] + y_offset
    
def draw_fixation(Image_file, fixation_df, offset):
    """Draw fixations on an image.
    Parameters
    ----------
    Image_file : str
        filename for the image where fixations will be imposed, e.g. "002-AI-261997-2648858.jpg"
    fixations : python list
        a list of fixations including x_cord, y_cord and duration
    """

    im = Image.open(Image_file)
    draw = ImageDraw.Draw(im, 'RGBA')

    x0, y0 = fixation_df['x_cord'][0] + offset[0], fixation_df['y_cord'][0] + offset[1]
    
    for row in fixation_df.itertuples(index=True, name='Pandas'):
        r = 8
        x = row.x_cord + offset[0]
        y = row.y_cord + int(offset[1])

        bound = (x - r, y - r, x + r, y + r)
        outline_color = (50, 255, 0, 0)
        fill_color = (50, 255, 0, 220)
        draw.ellipse(bound, fill=fill_color, outline=outline_color)

        bound = (x0, y0, x, y)
        line_color = (255, 155, 0, 155)
        penwidth = 2
        draw.line(bound, fill=line_color, width=5)

        x0, y0 = x, y

    plt.figure(figsize=(17, 15))
    plt.imshow(np.asarray(im), interpolation='nearest')

    # if len(fixations[0]) == 3:
    #     x0, y0, duration = fixations[0]
    # else:
    #     x0, y0 = fixations[0]

    # for fixation in fixations:
    #     r = 8
    #     x = fixation[0]
    #     y = fixation[1]

    #     bound = (x - r, y - r, x + r, y + r)
    #     outline_color = (50, 255, 0, 0)
    #     fill_color = (50, 255, 0, 220)
    #     draw.ellipse(bound, fill=fill_color, outline=outline_color)

    #     bound = (x0, y0, x, y)
    #     line_color = (255, 155, 0, 155)
    #     penwidth = 2
    #     draw.line(bound, fill=line_color, width=5)

    #     x0, y0 = x, y

    

def overlap(fix, AOI, offset, radius=25):
    """Checks if fixation is within radius distance or over an AOI. Returns True/False.
    Parameters
    ----------
    fix : Fixation
        A single fixation in a trial being considered for overlapping with the AOI
    AOI : pandas.DataFrame
        contains AOI #kind	name	x	y	width	height	local_id	image	token
    radius : int, optional
        radius around AOI to consider fixations in it within the AOI.
        default is 25 pixel since the fixation filter groups samples within 25 pixels.
    Returns
    -------
    bool
        whether it overlaps
    """

    box_x = AOI.aoi_x - (radius / 2)
    box_y = AOI.aoi_y - (radius / 2)
    box_w = AOI.aoi_width + (radius / 2)
    box_h = AOI.aoi_height + (radius / 2)

    return box_x <= fix.x_cord + offset[0] <= box_x + box_w and box_y <= fix.y_cord + offset[1] <= box_y + box_h

def hit_test(fixations, aois_tokens, offset, participant_ID, trial, time_stamp, radius=25):
    """Match fixations to AOIs to calculate the fixation duration over each AOI
    Parameters
    ----------
    fixations : list of list
        a list of fixations including x_cord, y_cord and duration
    aois_tokens : pandas.DataFrame
        contains AOI #kind	name	x	y	width	height	local_id	image	token
    radius : int, optional
        the area around the AOI included in the AOI region
    Returns
    -------
    pandas.DataFrame
        a dataframe of AOIs with fixation duration information
    """
    
    header = ["participant_ID",
             "trial",
             "time_stamp", 
              "duration",
              "x_cord",
              "y_cord",
              "aoi_x",
              "aoi_y",
              "aoi_width",
              "aoi_height",
              "image"
             ]

    result = pd.DataFrame(columns=header)
    
    for row in aois_tokens.itertuples(index=True, name='Pandas'):
            # kind	name	x	y	width	height	local_id	image	token

        if overlap(fixations, row, offset, radius):
            df = pd.DataFrame([[participant_ID,
                                trial,
                                time_stamp,
                              fixations.duration,
                                fixations.x_cord,
                                fixations.y_cord,
                                row.aoi_x,
                                row.aoi_y,
                                row.aoi_width,
                                row.aoi_height,
                                row.image] ], columns=header)
            return df

    return result