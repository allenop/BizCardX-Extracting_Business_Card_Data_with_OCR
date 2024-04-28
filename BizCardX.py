
import streamlit as st
from streamlit_option_menu import option_menu
from PIL import Image
import easyocr
import pandas as pd
import numpy as np
import re
import io
import mysql.connector

#SQL
myDb = mysql.connector.connect(
    user = 'root',
    host = 'localhost',
    password = 'Aa12345678!',
    database = 'biz_card')
myCursor = myDb.cursor()

#Create Table function
def create_table():
    create_query = ''' CREATE TABLE IF NOT EXISTS biz_card_details(name varchar(255),
                                                     designation VARCHAR(255),
                                                     company_name VARCHAR(255),
                                                     contact VARCHAR(255),
                                                     email  VARCHAR(255),
                                                     website  VARCHAR(255),
                                                     address  TEXT,
                                                     pincode INT,
                                                     image MEDIUMBLOB)'''
    
    myDb.commit()
    myCursor.execute(create_query)

#OCR Function 
def img_to_text(path):
    img_input = Image.open(path)
    img_arr = np.array(img_input)
    reader = easyocr.Reader(['en'])    
    text = reader.readtext(img_arr,detail = 0)
    return img_input, text

# Converting Image to Bytes
def img_to_bytes(img_input):
    img_bytes = io.BytesIO() 
    img_input.save(img_bytes, format = 'PNG')
    img_data = img_bytes.getvalue()
    return img_data

#Converting into Dataframe
def text_to_df(img_input,img_text):
    skl_dict = dict(Name = [],Designation = [],Company_Name = [],Contact = [],Email = [], Website = [], Address = [], Pincode = [],Image = [])
    for i,data in enumerate(img_text):
        if(i == 0):
            skl_dict['Name'].append(img_text[0])
        elif(i == 1):
            skl_dict['Designation'].append(img_text[1])
        elif data.startswith('+') or ("-" in data and data.replace('-','').isdigit()): 
            skl_dict['Contact'].append(data)
        elif "@" in data  and (".com" or "in" in data):
            skl_dict['Email'].append(data)
        elif "www" in data.lower():
            website = data.lower()
            skl_dict["Website"].append(website)
        elif re.search(r'[\d]{6}', data):
            match = re.findall(r'[\d]{6}', data)
            skl_dict['Pincode'].append(match[0])
        elif re.match(r'[A-za-z]+',data):
            skl_dict["Company_Name"].append(data)
        else:
            address = data.replace(',', '').replace(';','')
            address = ' '.join(address.split())
            skl_dict["Address"].append(address)
    
    # Pre Processing the data
    for key,value in skl_dict.items():
        if len(value) > 0:
            value = ' '.join(value) # Joining multiple value data into string
            skl_dict[key] = value
        else:
            skl_dict[key] = np.nan
    img_data = img_to_bytes(img_input)
    skl_dict['Image'] = (img_data)
    
    card_df = pd.DataFrame(skl_dict, index = [0])        
    return card_df

# Insert table function
def insert_table(card_df):
    insert_query = '''INSERT INTO biz_card_details
    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
    values = card_df.values.tolist()[0]
    myCursor.execute(insert_query,values)
    myDb.commit()
    
# Submit button func
def upload_button(card_df):
    create_table()
    insert_table(card_df)
    st.success('Data Uploaded Successfully')
    
# Select Table Function
def select_table():
    select_query = 'SELECT * FROM biz_card_details'
    myCursor.execute(select_query)
    bcd_df = pd.DataFrame(myCursor.fetchall(),columns = ['name','designation','company_name','contact','email','website','address','pincode','image'])
    return bcd_df

# Modify button func
def modify_table(selected_name,mod_df):
    delete_query = f'''DELETE from biz_card_details
                     WHERE Name = '{selected_name}'
                     '''
    myCursor.execute(delete_query)
    myDb.commit()
    insert_table(mod_df)
    st.success('Data Modified Successfully')

#Delete button func
def delete_button(selected_name, selected_designation):
    delete_query = f"DELETE FROM biz_card_details WHERE name = '{selected_name}' AND designation = '{selected_designation}'"
    myCursor.execute(delete_query)
    myDb.commit()
    st.success("Data deleted successfully")

# Streamlit part
icon = Image.open("icon.png") 
st.set_page_config(page_title= "BizCardX: Extracting Business Card Data with OCR",
                   page_icon= icon, #Title image
                   layout= "wide",
                   initial_sidebar_state= "expanded",
                   menu_items={'About': """# This OCR app is created by *Allen*!"""})
def setting_bg():
    wallpaper_url = 'https://img.freepik.com/free-vector/hand-painted-watercolor-pastel-sky-background_23-2148902771.jpg?size=626&ext=jpg&ga=GA1.1.553209589.1713657600&semt=sph'
    st.markdown(f""" <style>.stApp {{
                        background: url('{wallpaper_url}');
                        background-size: cover;}}
                     </style>""",unsafe_allow_html=True)

setting_bg()

st.markdown("<h1 style='text-align: center; background-color: pink; color : violet'>BizCardX: Extracting Business Card Data with OCR</h1>", unsafe_allow_html=True)


with st.sidebar: 
    side_nav = option_menu("MainMenu",["Home", "Upload, Modify and Delete"], 
                       icons=["house","cloud-upload","pencil-square"],
                       default_index=0,
                       #orientation="horizontal",
                       styles={"nav-link": {"font-size": "15px", "text-align": "centre", "margin": "0px", "--hover-color": "#6495ED"},
                               "nav-link-selected": {"background-color": "#6495ED"}})

    

if side_nav == 'Home':
    col1,col2 = st.columns(2)
    with col1:
        st.markdown("## :green[**Technologies Used :**] Python,easy OCR, Streamlit, SQL, Pandas")
        st.markdown("## :green[**Overview :**] In this streamlit web app you can upload an image of a business card and extract relevant information from it using easyOCR. You can view, modify or delete the extracted data in this app. This app would also allow users to save the extracted information into a database along with the uploaded business card image. The database would be able to store multiple entries, each with its own business card image and extracted information.")
    with col2:
        st.image("home.png")

elif side_nav == 'Upload, Modify and Delete':
    tab1,tab2,tab3 = st.tabs(['#### :blue[Upload]','#### :blue[Modify]','#### :blue[Delete]'])
    
    with tab1:
        col1, col2 = st.columns([0.6,0.4])
        with col1:
            img_input = st.file_uploader("#### :red[Upload Image]", type = ['png','jpg','jpeg'])
        if(img_input is not None):
            with col2:
                st.image(img_input, width = 400)
            with st.spinner('Please Wait for it...'):
                img_input, img_text = img_to_text(img_input)
                card_df = text_to_df(img_input,img_text)
                st.dataframe(card_df)
            if st.button (' :blue[Upload]'):
                with st.spinner('Please Wait for it...'):
                    upload_button(card_df)
        else:
            #st.warning("#### :red[Upload the Biz Card]")
            pass
        
    
    with tab2:
        bcd_df = select_table()
        selected_name = st.selectbox('Select a Name to Modify the Biz Card',bcd_df['name'].tolist())
        df_name = bcd_df.loc[bcd_df['name'] == selected_name]
        mod_df = df_name.copy() # Creating a df copy for modified values
        img_byte = df_name['image'].unique()[0]
        image = Image.open(io.BytesIO(img_byte))
        st.image(image, width = 400)
        
        col1, col2, col3 = st.columns(3, gap= 'medium')        
        with col1:
            mod_name = st.text_input('Modify the Name',df_name.name.unique()[0])# passing the parameter as a value instead of df or array
            mod_contact = st.text_input('Modify the Contact',df_name['contact'].unique()[0])
        
        with col2:
            mod_designation = st.text_input('Modify the Designation',df_name.designation.unique()[0])
            mod_email = st.text_input('Modify the Email',df_name['email'].unique()[0])
            
        with col3:
            mod_company_name = st.text_input('Modify the Company Name',df_name['company_name'].unique()[0])
            mod_website = st.text_input('Modify the Website',df_name['website'].unique()[0])    
        mod_address = st.text_input('Modify the Address',df_name['address'].unique()[0])
        mod_pincode = st.text_input('Modify the Pincode',df_name['pincode'].unique()[0])
        
        mod_df['name'] = mod_name
        mod_df['designation'] = mod_designation 
        mod_df['company_name'] = mod_company_name
        mod_df['contact'] = mod_contact
        mod_df['email'] = mod_email
        mod_df['website'] = mod_website
        mod_df['address'] = mod_address
        mod_df['pincode'] = mod_pincode
        st.markdown('### :green[Actual Table]')
        st.dataframe(df_name)
        st.markdown('### :green[Modified Table]')
        st.dataframe(mod_df)
        
        if st.button('## :blue[Modify]'):
            modify_table(selected_name,mod_df)
    with tab3:
        bcd_df = select_table()
        #st.dataframe(bcd_df)
        col1, col2 = st.columns(2)
        with col1:
            selected_name = st.selectbox('Select the Name',bcd_df.name)
            df_name = bcd_df.loc[bcd_df.name == selected_name]
        with col2:
            selected_designation = st.selectbox('Select the Designation',df_name.designation)
            df_name_desig = df_name.loc[df_name.designation == selected_designation]
        st.markdown('### :red[Data to be Deleted ]')
        st.dataframe(df_name_desig)
        
        if st.button('## :blue[Delete]'):
            delete_button(selected_name,selected_designation)
        
        
                    
                           
                                       
                                       
                                       
                                       
        
                                       
                                       
                                       
                                       
                                       
                                       
        
                                       
                                       
                                       
            
    
