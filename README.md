- alias: power check
  trigger:
    platform: mqtt
    topic: "ha/tts/google_translate_say"
  action:
    - data:
        language: "{{ value_json['speech'].language }}"
        message: "{{ value_json['speech'].message }}"
      service: tts.google_translate_say    
      entity_id: "{{ value_json['speech'].entity_id }}"

mosquitto_pub -h 192.168.147.1 -t ha/tts/google_translate_say -m '{"time": "2020-07-25T16:41:52", "speech": {"entity_id": "media_player.entryway", "language": "it", "message": "la potenza sta salendo al 52 percento"}}'