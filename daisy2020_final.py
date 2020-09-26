import os, io
from google.cloud import vision 
from google.cloud.vision import types
import json, csv
import numpy as np 

class Products:
    def __init__(self):
        # Excel importing 
        with open('product_dictionary.csv', 'r') as f:
            self.productList = [line.rstrip('\n') for line in f]
        self.productList.sort()
        
        for i in range(len(self.productList)):
            self.productList[i] = self.productList[i].split()

        # Read unit dictionary as list
        with open('units_dictionary.csv', 'r') as f:
            self.unitsList = [line.rstrip('\n') for line in f]

        self.unitsList.sort()

        for i in range(len(self.unitsList)):
            self.unitsList[i] = self.unitsList[i].split()
        return

    def check_bound(self,texts, x_bound, y_bound,names):
        for text in texts[1:]:
            vertices = ([[float(vertex.x), float(vertex.y)] for vertex in text.bounding_poly.vertices])
            # print(text.description,vertices)
            for i in range(len(x_bound)):
                if vertices[0][0] > x_bound[i][0] and vertices[1][0] < x_bound[i][1] and vertices[0][1] >= y_bound[i][0] and vertices[2][1] <= y_bound[i][1]:
                    if names[i] == None:
                        names[i] = text.description
                    else:
                        names[i] += ' ' + text.description
        return names 
        
    def set_bound(self,texts):
        names = []
        x_bound = []
        y_bound = []
        redBound_x = []
        redBound_y = []
        for text in texts[1:]:
            if "$" in text.description or "SAVE" in text.description or "HALF" in text.description or "BUY" in text.description or "%" in text.description or "¢" in text.description: 
                text.description = text.description.replace('\n',' ')
                text.description = text.description.replace('"','\"')

                x = ([float(vertex.x) for vertex in text.bounding_poly.vertices])
                y = ([float(vertex.y) for vertex in text.bounding_poly.vertices])
                box = list(x)+list(y)

                x_bound.append([box[0] - 400,box[1] + 400])
                y_bound.append([box[4]-10,box[-1] + 500])
                redBound_x.append([box[0],box[1] + 240])
                redBound_y.append([box[4]-10,box[-1] + 100])

                names.append(text.description)

        return [names,x_bound,y_bound,redBound_x,redBound_y]

    def setup(self,FILE_NAME,FOLDER_PATH):
        client = vision.ImageAnnotatorClient()
        with io.open(os.path.join(FOLDER_PATH,FILE_NAME), 'rb') as image_file:
            content = image_file.read()
        image = vision.types.Image(content = content)
        response_text = client.text_detection(image=image)
        if response_text.error.message:
            raise Exception(
                '{}\nFor more info on error messages, check: '
                'https://cloud.google.com/apis/design/errors'.format(
                    response_text.error.message))
        return response_text

    def weekly_adblocks(self,FOLDER_PATH,page):
        w_idx = FOLDER_PATH.find('w')
        week = (FOLDER_PATH[w_idx:])
        result = []

        #Red
        FILE_NAME = week + page + 'red.jpg'

        response_text = self.setup(FILE_NAME,FOLDER_PATH)
        redTexts = response_text.text_annotations     

        x_bound = []
        y_bound = []
        redBound_x = []
        redBound_y = []
        redNames = []

        redNames, x_bound, y_bound, redBound_x, redBound_y = self.set_bound(redTexts)

        redNames = self.check_bound(redTexts,redBound_x,redBound_y,redNames)

        #Black
        FILE_NAME = week + page + 'black.jpg'

        response_text = self.setup(FILE_NAME,FOLDER_PATH)
        blackTexts = response_text.text_annotations     

        productNames = [None]*len(x_bound)
        productNames = self.check_bound(blackTexts,x_bound,y_bound,productNames)

        #Grey 
        FILE_NAME = week + page + 'grey.jpg'

        response_text = self.setup(FILE_NAME,FOLDER_PATH)
        greyTexts = response_text.text_annotations     

        saveNames = [None]*len(x_bound)
        saveNames = self.check_bound(greyTexts,x_bound,y_bound,saveNames)

        # print(len(redNames),redNames)
        # print(len(productNames),productNames)
        # print(len(saveNames),saveNames)
        date = (FILE_NAME[:-9])
        result = ([date,redNames,saveNames,productNames])
        return result
    
    def convertBlackText(self,blackText, fileName):
        for i in range(len(blackText)):
            if blackText[i] == None:
                continue
            else:
                blackText[i] = blackText[i].split()
        # blackText = [text for text in blackText if text!=None]
        outputDicts = [None]*len(blackText)
        for i in range(len(blackText)):
            index = 0
            skip = False
            if blackText[i] == None:
                continue
            while not any(blackText[i][index] == s[0] for s in self.productList):
                # print(index,len(blackText),i)
                index += 1
                if index == len(blackText[i]):
                    skip = True
                    break
            if skip == True:
                continue
            productName = [blackText[i][index]]
            oldProductName = []
            foundOne = False
            outputDict = [None]*8
            checkIndex = 1
            while(checkIndex < len(blackText[i])):
                matching = [s for s in self.productList if s[0:checkIndex] == productName]
                # print(productName)
                # print(matching)
                if len(matching) == 0:
                    # print("old", oldProductName)
                    matching = [s for s in self.productList if s[0:checkIndex - 1] == oldProductName]
                    if foundOne == True:
                        separator = ' '
                        outputDict[0] = fileName
                        outputDict[1] = separator.join(matching[0])
                    break
                elif len(matching) == 1:
                    separator = ' '
                    outputDict[0] = fileName
                    outputDict[1] = separator.join(matching[0])
                    break
                else:
                    foundOne = True
                    index += 1
                    checkIndex += 1
                    oldProductName = list(productName)
                    # print(blackText[i])

                    if (blackText[i][0]) == '3:JY':
                        continue
                    if (blackText[i][0]) == 'ODcie':
                        continue
                    productName.append(blackText[i][index])
            outputDicts[i] = outputDict
        # print(outputDicts)
        # print(blackText)

        for i in range(len(blackText)):
            index = 0
            if blackText[i] == None or outputDicts[i] == None:
                continue
            while index < len(blackText[i]):
                # 1 pint
                if blackText[i][index].startswith('Pint'):
                    outputDicts[i][3] = blackText[i][index-1] + ' Pint'
                    break
                # 2 oz
                elif blackText[i][index].startswith('oz'):
                    if blackText[i][index].startswith('oz'):
                        outputDicts[i][3] = blackText[i][index-1] + ' oz'
                        break
                    # three different oz
                    elif blackText[i][index-2] == '&':
                        outputDicts[i][3] = blackText[i][index-4:index-1] + ' oz'
                        break
                    # No space before oz
                    else:
                        ozIndex = blackText[i][index].find('oz')
                        outputDicts[i][3] = blackText[i][index][:ozIndex] + ' oz'
                        break
                elif blackText[i][index].startswith('Pack'):
                    if blackText[i][index].startswith('Packed'):
                        continue
                    # 3 can
                    if blackText[i][index+1].startswith('Cans'):
                        outputDicts[i][3] = blackText[i][index-1] + ' can'
                        break
                    # 4 package
                    elif blackText[i][index+1].startswith('Package') or blackText[i][index+1].startswith('package'):
                        outputDicts[i][3] = blackText[i][index-1] + ' package'
                        break
                    # 5 Pack(s)
                    else:
                        outputDicts[i][3] = blackText[i][index-1] + ' pack'
                        break
                # 6 mL
                elif blackText[i][index].startswith('mL'):
                    outputDicts[i][3] = blackText[i][index-1] + ' ml'
                    break
                # 7 Liter
                elif blackText[i][index].startswith('Liter'):
                    outputDicts[i][3] = blackText[i][index-1] + ' liter'
                    break
                # 8 Gallon
                elif blackText[i][index].startswith('Gallon'):
                    outputDicts[i][3] = blackText[i][index-1] + ' gallon'
                    break
                # 9 lbs (added later)
                # 10 bag
                elif blackText[i][index].startswith('Bag') or blackText[i][index].startswith('bag'):
                    outputDicts[i][3] = blackText[i][index-1] + ' bag'
                    break
                # 11 capsule
                elif blackText[i][index].startswith('Capsule') or blackText[i][index].startswith('capsule'):
                    outputDicts[i][3] = blackText[i][index-1] + ' capsule'
                    break
                # 12 g
                elif blackText[i][index].startswith('Gram') or blackText[i][index].startswith('gram') or blackText[i][index] == 'g':
                    outputDicts[i][3] = blackText[i][index-1] + ' g'
                    break
                # 13 pk
                elif blackText[i][index].startswith('Pk') or blackText[i][index].startswith('pk'):
                    outputDicts[i][3] = blackText[i][index-1] + ' pk'
                    break
                # 14 pt
                elif blackText[i][index].startswith('Pt') or blackText[i][index].startswith('pt'):
                    outputDicts[i][3] = blackText[i][index-1] + ' pt'
                    break
                # 15 quart
                elif blackText[i][index].startswith('Quart') or blackText[i][index].startswith('quart'):
                    outputDicts[i][3] = blackText[i][index-1] + ' quart'
                    break
                # 16 serving
                elif blackText[i][index].startswith('Serving') or blackText[i][index].startswith('serving'):
                    outputDicts[i][3] = blackText[i][index-1] + ' serving'
                    break
                # 17 tablet
                elif blackText[i][index].startswith('Tablet') or blackText[i][index].startswith('tablet'):
                    outputDicts[i][3] = blackText[i][index-1] + ' tablet'
                    break
                # 18 inch
                elif blackText[i][index].startswith('Inch') or blackText[i][index].startswith('inch') or blackText[i][index] == 'in.':
                    outputDicts[i][3] = blackText[i][index-1] + ' inch'
                    break
                else:
                    index += 1
        # print(outputDicts)

        return outputDicts

    def convertRedText(self,redText, grayText, outputDicts):
        for i in range(len(redText)):
            # Red Text
            if outputDicts[i] != None and outputDicts[i][1] != None:
                if 'Organic' in outputDicts[i][1]:
                    outputDicts[i][7] = 1
                else:
                    # print("", outputDicts[i])
                    outputDicts[i][7] = 0
            else:
                continue
            # redText contains '$'
            if '$' in redText[i]:
                # redText contains '/lb'
                if '/lb' in redText[i]:
                    # SAVE $11/lb.
                    if 'SAVE' in redText[i]:
                        outputDicts[i][3] = 'lb'
                        outputDicts[i][4] = 1
                        dollarIndex = redText[i].find('$')
                        slashIndex = redText[i].find('/')
                        if dollarIndex == -1 or slashIndex == -1:
                            continue
                        outputDicts[i][5] = redText[i][dollarIndex+1:slashIndex]
                    # $699/lb.
                    else:
                        spaceIndex = redText[i].find(' ')
                        if spaceIndex != -1:
                            redText[i] = redText[i][:spaceIndex]
                        outputDicts[i][3] = 'lb'
                        outputDicts[i][4] = 1
                        dollarIndex = redText[i].find('$')
                        slashIndex = redText[i].find('/')
                        if dollarIndex == -1 or slashIndex == -1:
                            continue
                        outputDicts[i][2] = redText[i][dollarIndex+1:slashIndex-2] + '.' + redText[i][slashIndex-2:slashIndex]

                # redText contains 'OFF'
                elif 'OFF' in redText[i]:
                    # $3 OFF PER POUND
                    if 'OFF PER POUND' in redText[i]:
                        outputDicts[i][3] = 'lb'
                        outputDicts[i][4] = 1
                        dollarIndex = redText[i].find('$')
                        spaceIndex = redText[i].find(' ')
                        if dollarIndex == -1 or spaceIndex == -1:
                            continue
                        outputDicts[i][2] = redText[i][dollarIndex+1:spaceIndex]
                    # $1 OFF
                    else:
                        outputDicts[i][4] = 1
                        dollarIndex = redText[i].find('$')
                        spaceIndex = redText[i].find(' ')
                        if dollarIndex == -1 or spaceIndex == -1:
                            continue
                        outputDicts[i][5] = redText[i][dollarIndex+1:spaceIndex]

                # 2/$5
                elif '/$' in redText[i]:
                    spaceIndex = redText[i].find(' ')
                    if spaceIndex != -1:
                        redText[i] = redText[i][:spaceIndex]
                    dollarIndex = redText[i].find('$')
                    slashIndex = redText[i].find('/')
                    if dollarIndex == -1 or slashIndex == -1:
                        continue
                    outputDicts[i][4] = redText[i][:dollarIndex-1]
                    print(redText[i])
                    if (redText[i] == '2/$5,'):
                        outputDicts[i][2] = 2.5
                    else:
                        price = float(redText[i][dollarIndex+1:])
                        promoPrice  = price / int(outputDicts[i][4])
                        outputDicts[i][2] = promoPrice

                # $599/Pack
                elif '/Pack' in redText[i]:
                    spaceIndex = redText[i].find(' ')
                    if spaceIndex != -1:
                        redText[i] = redText[i][:spaceIndex]
                    outputDicts[i][3] = '1 Pack'
                    outputDicts[i][4] = 1
                    dollarIndex = redText[i].find('$')
                    slashIndex = redText[i].find('/')
                    if dollarIndex == -1 or slashIndex == -1:
                        continue
                    outputDicts[i][2] = redText[i][dollarIndex+1:slashIndex-2] + '.' + redText[i][slashIndex-2:slashIndex]
                
                # $399
                else:
                    spaceIndex = redText[i].find(' ')
                    if spaceIndex != -1:
                        redText[i] = redText[i][:spaceIndex]
                    outputDicts[i][4] = 1
                    dollarIndex = redText[i].find('$')
                    if dollarIndex == -1:
                        continue
                    outputDicts[i][2] = redText[i][dollarIndex+1:-2] + '.' + redText[i][-2:]

            # redText contains '¢'
            elif '¢' in redText[i]:
                # 99¢/lb.
                if '/lb' in redText[i]:
                    spaceIndex = redText[i].find(' ')
                    if spaceIndex != -1:
                        redText[i] = redText[i][:spaceIndex]
                    outputDicts[i][3] = 'lb'
                    outputDicts[i][4] = 1
                    centIndex = redText[i].find('¢')
                    slashIndex = redText[i].find('/')
                    if centIndex == -1 or slashIndex == -1:
                        continue
                    outputDicts[i][2] = '.' + redText[i][:centIndex]
        
                # 99¢
                else:
                    spaceIndex = redText[i].find(' ')
                    if spaceIndex != -1:
                        redText[i] = redText[i][:spaceIndex]
                    outputDicts[i][4] = 1
                    centIndex = redText[i].find('¢')
                    if centIndex == -1:
                        continue
                    outputDicts[i][2] = '.' + redText[i][:centIndex]

            # redText contains 'OFF'
            elif 'OFF' in redText[i]:
                # HALF OFF!
                if 'HALF OFF' in redText[i]:
                    outputDicts[i][4] = 1
                    outputDicts[i][6] = 0.5

                # 10% OFF
                elif '% OFF' in redText[i]:
                    outputDicts[i][4] = 1
                    percentIndex = redText[i].find('%')
                    if percentIndex == -1:
                        continue
                    outputDicts[i][6] = '.' + redText[i][:percentIndex]
            
            # BUY ONE, GET ONE FREE
            elif 'BUY ONE':
                outputDicts[i][4] = 2
                outputDicts[i][6] = 0.5

            # Gray Text
            grayitem = grayText[i]
            if grayitem == None:
                continue

            if 'SAVE' in grayitem:
                save_ind =  grayitem.find('SAVE')
                if grayitem[save_ind+4::].find('SAVE') != -1:
                    grayitem = grayitem[0:save_ind+4+grayitem[save_ind+4::].find('SAVE')]

                if '$' in grayitem:
                    dollarIndex = grayitem.find('$')
                    dollar_space_Idx = grayitem[dollarIndex+1::].find(' ')
                    saved_amount = grayitem[dollarIndex + 1:dollarIndex+dollar_space_Idx+1]
                    if dollar_space_Idx == -1:
                        saved_amount = grayitem[dollarIndex + 1::]
                    outputDicts[i][4] = 1

                    if not saved_amount.isnumeric():
                        if '/' in saved_amount:
                            slashIndex = saved_amount.find('/')
                            new_saved_amount = saved_amount[0:slashIndex]
                            if saved_amount[slashIndex+1].isnumeric():
                                outputDicts[i][4] = saved_amount[slashIndex+1]
                            saved_amount = new_saved_amount
                    try:
                        outputDicts[i][5] = float(saved_amount)/float(outputDicts[i][4])
                    except:
                        pass


                elif '¢' in grayitem or 'c' in grayitem or 'C' in grayitem:
                    if grayitem.find('c') != -1 and grayitem[grayitem.find('c')-1].isnumeric():
                        centIndex = grayitem.find('c')
                    elif grayitem.find('C') != -1 and grayitem[grayitem.find('C')-1].isnumeric():
                        centIndex = grayitem.find('C')
                    else:    
                        centIndex = grayitem.find('¢')
                    
                    cent_space_Idx = grayitem[0:centIndex].find(' ')
                    saved_amount = grayitem[cent_space_Idx+ 1:centIndex]
                    outputDicts[i][4] = 1

                    if not saved_amount.isnumeric():
                        if '/' in saved_amount:
                            slashIndex = saved_amount.find('/')
                            new_saved_amount = saved_amount[0:slashIndex]
                            if saved_amount[slashIndex + 1].isnumeric():
                                outputDicts[i][4] = saved_amount[slashIndex + 1]
                            saved_amount = new_saved_amount
                    try:
                        outputDicts[i][5] = float(saved_amount)/(float(outputDicts[i][4])*100)
                    except:
                        pass

                if 'on' in grayitem:
                    onIndex = grayitem.find('on')
                    if grayitem[onIndex-1] != ' ' or grayitem[onIndex+1] != ' ':
                        break

                    on_space_Idx = grayitem[onIndex + 3::].find(' ')
                    quality_savings_for = grayitem[onIndex + 3: onIndex +3 + on_space_Idx + 1]
                    if on_space_Idx == -1:
                        quality_savings_for = grayitem[onIndex + 3::]
                    outputDicts[i][4] = quality_savings_for

                    try:
                        outputDicts[i][5] = float(outputDicts[i][5]) / float(quality_savings_for)
                    except:
                        pass

            # Calculate discount
            if (outputDicts[i][5] != None) and (outputDicts[i][2] != None):
                try:
                    outputDicts[i][6] = round((float(outputDicts[i][5])/(float(outputDicts[i][2]) + float(outputDicts[i][5]))),2)
                except:
                    pass
        return outputDicts

if __name__ == "__main__":
    np.set_printoptions(threshold=np.inf)
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'ServiceAccToken.json'
    """ Parse the red, black, and gray files for blocks """
    path_names = ['/home/trudie/Documents/daisy-champions/3_color_dir/week_1',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_2',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_3',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_4',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_5',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_6',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_7',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_8',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_9',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_10',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_11',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_12',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_13',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_14',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_15',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_16',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_17',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_18',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_19',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_20',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_21',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_22',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_23',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_24',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_25',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_26',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_27',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_28',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_29',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_30',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_31',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_32',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_33',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_34',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_35',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_36',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_37',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_38',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_39',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_40',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_41',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_42',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_43',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_44',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_45',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_46',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_47',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_48',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_49',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_50',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_51',
        '/home/trudie/Documents/daisy-champions/3_color_dir/week_52']

    products = Products()
    pages = ['_page_1_','_page_2_','_page_3_','_page_4_']
        
    # Write to csv
    csv_columns = ['flyer_name', 'product_name', 'unit_promo_price', 'uom', 'least_unit_for_promo', 'save_per_unit', 'discount', 'organic']

    with open('output.csv', 'w', encoding='utf8', newline='') as output_file:
        fc = csv.writer(output_file)
        fc.writerow(csv_columns)
        for i in range(6,7): #6, 25
            result = []
            for page in pages[0:3]:
                result = products.weekly_adblocks(path_names[i],page)
                outputDicts = products.convertBlackText(result[3], result[0])
                outputDicts = products.convertRedText(result[1], result[2], outputDicts)
                for j in range(len(outputDicts)):
                    if (outputDicts[j] == None):
                        continue
                    else:
                        fc.writerow(outputDicts[j])    
