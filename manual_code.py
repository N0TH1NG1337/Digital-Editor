"""
This file is not official part of the Digital Editor project, but a side script for showcase.

In some cases writing manually the whole project code can be a problem.

This script can get the project code. Parse it into values and use to build
the project code on other machine.
"""

import base64

def main( ):
    
    exit = False

    while not exit:
        print( "Select option for convert." )
        print( "1: Convert code into values" )
        print( "2: Convert values into code" )
        print( "3: Exit" )

        mode = input( "Mode : " )

        try:
            mode_type: int = int( mode )

            if mode_type == 1:
                # Convert code into values
                project_code: str = input( "Enter project code : " )

                decoded_value:  str     = base64.b64decode( project_code.encode( ) ).decode( )
                values_list:    list    = decoded_value.split( ":" )

                print( f"Ip value:      { values_list[ 0 ] }" )
                print( f"Port value:    { values_list[ 1 ] }" )

            
            if mode_type == 2:
                # Convert values into code
                ip_value    = input( "Enter IP value : " )
                port_value  = input( "Enter Port value : " )

                format_value:   str = f"{ ip_value }:{ port_value }"
                encoded_value:  str = base64.b64encode( format_value.encode( ) ).decode( )
                
                print( "Result code: " )
                print( encoded_value )

            
            if mode_type == 3:
                exit = True

        except:
            print( "Invalid mode type" )

if __name__ == "__main__":
    main( )