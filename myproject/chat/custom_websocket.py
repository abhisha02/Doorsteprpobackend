from channels.generic.websocket import AsyncWebsocketConsumer

class CustomAsyncWebsocketConsumer(AsyncWebsocketConsumer):
    async def websocket_receive(self, event):
        print(f"websocket_receive called with event: {event}")
        try:
            if "text" in event:
                await self.receive(text_data=event["text"])
            elif "bytes" in event:
                await self.receive(bytes_data=event["bytes"])
            else:
                print(f"Unexpected event format: {event}")
        except Exception as e:
            print(f"Exception in websocket_receive: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")