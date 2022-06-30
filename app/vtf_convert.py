import texture2ddecoder, os
from PIL import Image

def get_image_data(vtf_file_bytes, vtf_dims, high_res_img_format):
    mipmap_count = vtf_file_bytes[56]
    largest_mipmap_dims = vtf_dims
    largest_mipmap_bytes = None
    high_res_img_data = None
    
    if high_res_img_format == 15: # DXT5 compression
        largest_mipmap_bytes = (largest_mipmap_dims[0]*largest_mipmap_dims[1]) # DXT5 stores each pixel as a byte, so a 16px by 16px mipmap would have an area of 256 bytes, for example
        
    elif high_res_img_format == 12: # BGRA32
        largest_mipmap_bytes = (largest_mipmap_dims[0]*largest_mipmap_dims[1]*4) # BGRA32 assigns 1 byte to each color channel for 32 bits (4 bytes) per pixel
        
    elif high_res_img_format == 1: # ABRG32
        largest_mipmap_bytes = (largest_mipmap_dims[0]*largest_mipmap_dims[1]*4) # ABRG32 assigns 1 byte to each color channel for 32 bits (4 bytes) per pixel
        
    elif high_res_img_format == 0: # RGBA32
        largest_mipmap_bytes = (largest_mipmap_dims[0]*largest_mipmap_dims[1]*4) # RGBA32 assigns 1 byte to each color channel for 32 bits (4 bytes) per pixel
        
    high_res_img_data = vtf_file_bytes[-largest_mipmap_bytes:] # Since largest mipmap always comes last in VTFs, slice vtf_file_bytes (a list) such that only the last largest_mipmap_bytes remain
    return high_res_img_data


# @param vtf_file - a VTF file
# @returns - a PNG Image of the VTF
def vtf2png(vtf_file):
    vtf_file_bytes = open(vtf_file,'rb').read() 
    vtf_width = vtf_file_bytes[16]
    vtf_height = vtf_file_bytes[18]
    high_res_img_format = vtf_file_bytes[52]
    png_img = None
    
    if high_res_img_format == 15: # 15 for DXT5
       
        compressed_img_hex = get_image_data(vtf_file_bytes, (vtf_width,vtf_height), high_res_img_format)
        decompressed_img_hex = texture2ddecoder.decode_bc3(compressed_img_hex, vtf_width, vtf_height) # Decompresses DXT5 (BC3) bytes, returns BGRA bytes
        png_img = Image.frombytes("RGBA", (vtf_width, vtf_height), decompressed_img_hex, 'raw', ("BGRA")) # Creating an RGBA image from BGRA bytes
        png_img = png_img.resize((64,64))
        
    elif high_res_img_format == 12: # 12 for BGRA32
        bgra32_img_hex = get_image_data(vtf_file_bytes, (vtf_width,vtf_height), high_res_img_format)
        bgra32_img_dec = [hex for hex in bgra32_img_hex] # Converting hexadecimal->decimal for actual numbers to be used in determining pixel colors
        
        # Since BGRA32 stores each pixel in 4 bytes, create 4-byte chunks from raw decimal color data (a list) to represent each pixel
        start = 0
        stop = 4
        bgra32_img_pixels = []
        for i in range(len(bgra32_img_dec)//4):
            bgra32_img_pixels.append(bgra32_img_dec[start:stop])
            start = stop
            stop += 4
               
        png_img = Image.new("RGBA",(vtf_width,vtf_height))
        rgba_image_pixels = []
        for bgra_pixel in bgra32_img_pixels:
            # Swapping blue and red color channels in each pixel to convert BGRA->RGBA, then making a PNG image with those converted pixel
            blue = bgra_pixel[0]
            red = bgra_pixel[2]
            bgra_pixel[0] = red
            bgra_pixel[2] = blue
            rgba_image_pixels.append(tuple(bgra_pixel))
        png_img.putdata(rgba_image_pixels)
        png_img = png_img.resize((64,64))
        
    elif high_res_img_format == 1: # 1 for ABRG32
        abrg32_img_hex = get_image_data(vtf_file_bytes, (vtf_width,vtf_height), high_res_img_format)
        abrg32_img_dec = [hex for hex in abrg32_img_hex] # Converting hexadecimal->decimal for actual numbers to be used in determining pixel colors
        
        # Since ABRG32 stores each pixel in 4 bytes, create 4-byte chunks from raw decimal color data (a list) to represent each pixel
        start = 0
        stop = 4
        image_data = []
        for i in range(len(abrg32_img_dec)//4):
            image_data.append(abrg32_img_dec[start:stop])
            start = stop
            stop += 4
        
        png_img = Image.new("RGBA",(vtf_width,vtf_height))
        rgba_image_pixels = []
        for abrg_pixel in image_data:
            # first swapping A and G to go from ABRG->GBRA
            alpha = abrg_pixel[0]
            green = abrg_pixel[3]
            abrg_pixel[0] = green
            abrg_pixel[3] = alpha
        
            # then swapping G and R to go from GBRA->RBGA
            green = abrg_pixel[0]
            red = abrg_pixel[2]
            abrg_pixel[0] = red
            abrg_pixel[2] = green
            
            # then swapping B and G to go from RBGA->RGBA
            blue = abrg_pixel[1]
            green = abrg_pixel[2]
            abrg_pixel[1] = green
            abrg_pixel[2] = blue
            rgba_image_pixels.append(tuple(abrg_pixel))
        png_img.putdata(rgba_image_pixels)
        png_img = png_img.resize((64,64))
     
    elif high_res_img_format == 0: # 0 for RGBA32
        rgba32_img_hex = get_image_data(vtf_file_bytes, (vtf_width,vtf_height), high_res_img_format)
        rgba32_img_dec = [hex for hex in rgba32_img_hex] # Converting hexadecimal->decimal for actual numbers to be used in determining pixel colors
        
        # Since RGBA32 stores each pixel in 4 bytes, create 4-byte chunks from raw decimal color data (a list) to represent each pixel
        start = 0
        stop = 4
        image_data = []
        for i in range(len(rgba32_img_dec)//4):
            image_data.append(rgba32_img_dec[start:stop])
            start = stop
            stop += 4
        
        png_img = Image.new("RGBA",(vtf_width,vtf_height))
        rgba_image_pixels = []
        for rgba_pixel in image_data:
            rgba_image_pixels.append(tuple(rgba_pixel))
        png_img.putdata(rgba_image_pixels)
        png_img = png_img.resize((64,64))
        
    return png_img
    
    
# @param vtf_header_bytes - first 80 bytes of a VTF file
# @returns - True or False, depending on whether or not VTF file header checks out 
def validate_vtf_header(vtf_header_bytes):
    # TODO: restructure this so it isn't disgusting and hard to read
    # TODO: check additional pieces of header, such as highResImageFormat
    # Verifying the file signature
    file_signature = vtf_header_bytes[0:4]
    if file_signature == b'VTF\x00':
        version_numb = vtf_header_bytes[4:12]
        # Verifying VTF version (must be 7.2)
        if version_numb == b'\x07\x00\x00\x00\x02\x00\x00\x00':
            header_size = vtf_header_bytes[12]
            # Verifying header is 80 bytes in size
            if header_size == 80:
                vtf_height = vtf_header_bytes[16]
                vtf_width = vtf_header_bytes[18]
                # Verifying VTF height/width are powers of 2
                if (vtf_height%2==0) and (vtf_width%2==0):                    
                    vtf_depth = vtf_header_bytes[63]
                    # Verifying VTF is a 2D texture (depth=1 is an indication of this)
                    if vtf_depth == 1:
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                return False
        else:
            return False
    else:
        return False

