from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException
from pymodbus.pdu import ExceptionResponse

class EM112Reader:
    """ Class to read information from the Carlo Gavazzi EM112 smart meter """
    def __init__(self):
        self.client = ModbusSerialClient(port="/dev/ttyUSB0", method="rtu", baudrate=9600)

    def connect(self):
        self.client.connect()
        print(f"Connection Status: {str(self.client.is_socket_open())}")

    def close(self):
        self.client.close()

    def read(self, address):
        try:
            result = self.client.read_holding_registers(address=address, count=1, slave=0x02)
            #result = client.read_coils(address=0x00, count=2, slave=0x02)
        except ModbusException as exc:
            txt = "ERROR: exception in pymodbus {exc}"
            print(txt)
            raise exc
        
        if result.isError():
            txt = "ERROR: pymodbus returned an error! {result}"
            print(txt)
            raise ModbusException(txt)
        if isinstance(result, ExceptionResponse):
            txt = "ERROR: received exception from device {result}!"
            print(txt)
            # THIS IS NOT A PYTHON EXCEPTION, but a valid modbus message
            raise ModbusException(txt)
        
        #print("Read")
        #print(result.bits[0])
        txt = f"### Template coils response: {str(result)}"
        #print(txt)
        txt = f"### Template coils response: {str(result.registers)}"
        #print(txt)
        txt = f"### Template coils response: {str(result.registers[0])}"
        #print(txt)
        return result.registers[0]
