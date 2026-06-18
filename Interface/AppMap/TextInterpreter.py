
class InputInterpreter:
    def __init__(self, callback_handler):
        self.topic_split = "/"
        self.msg_split = ","
        self.callback_handler = callback_handler

    def check_if_robot_exists(self, robot_name):
        """Checks if a robot exists in the robotsDict."""
        if robot_name in self.callback_handler("get_robot_names"):
            return True
        return False


    def parse_message(self, decodedMessage, topic):
        """parses the incoming MQTT messages and checks if they are valid, if so updates the robot values and returns if a new marker needs to be placed.""" 
        splitTopic = topic.split(self.topic_split)
        msg_to_return = None
        #make a new robot if its not in the current list            
        msg_to_return =self._get_correct_output(name= splitTopic[1], valueField=splitTopic[2], value=decodedMessage)
        print("message to be returned in parsed message = ", msg_to_return)
        return msg_to_return
        
    
    def _get_correct_output(self, name, valueField, value):
        """updates the robot values and checks if a new marker needs to be placed, if so returns the marker info."""
        msg_to_return = []
        # robot positions need to be checked and if valid changed 
        if (valueField == "Position"):
            ###check if the positions message is valid
            checkedPositions = self._position_check(value)
            if checkedPositions:
                print("new positions to check = ", checkedPositions)
                msg_to_return = [name, valueField, checkedPositions[0], checkedPositions[1], checkedPositions[2] ]
        #pdate robot status 
        elif (valueField == "Status"):
            msg_to_return = [name, valueField,value]
        return msg_to_return

    def _position_check(self, position):
        """checks if the position message is valid(lat,lon,direction), if so returns the position info."""
        latAndLongDirection = position.split(self.msg_split)
        print(f"{latAndLongDirection}" + f"{len(latAndLongDirection)}")
        ### latitude, longitude and direction of NESW 
        if len(latAndLongDirection) == 3:
            ###check the lat, long and direction if they are valid 
            latitude = self._is_fLoat(latAndLongDirection[0])
            longitude = self._is_fLoat(latAndLongDirection[1])
            direction = self._is_direction(self._is_fLoat(latAndLongDirection[2]))
            print(f"{latitude}" + f"{longitude}" + f"{direction}")
            ### return the lat, long and dir if valid
            if latitude and longitude and direction:
                print("position check valid")
                return [latitude, longitude, direction] 
        return False

    def _is_fLoat(self, value):
        """checks if the value can be converted to a float, if so returns the float value."""
        try:
            return float(value)
        except Exception as e:
            print("EXCEPTION: ", e)
            return False

    def _is_direction(self, direction):
        """checks if the direction is a valid direction between 0 and 360, if so returns the direction value."""
        if(direction >= 0 and direction <=360):
            return direction
        return False
