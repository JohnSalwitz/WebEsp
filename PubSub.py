from ESPManager import esp_manager
from Logging import jlog
from TCLHandler import TCLHandler

# Titles (message names) and the associated scripts... sent to esps that subscribe
topics = {
    "cat_in_box": "run_cat_fan",
    "tool_loud": "start_dust_collector",
    "tool_quiet": "stop_dust_collector",
}


class PubSubBroker:

    @staticmethod
    def publish(title):
        """Transmits a topic to all subscribing esps.  passes topic title and foreground script. Ie: Subscribing to message
         will run script... """
        if title in topics:
            tcl_handler = TCLHandler()
            _, _, tcl = tcl_handler.load(topics[title])
            count = esp_manager.publish_to_esps(title, tcl)
            return count

        jlog.error("Unknown Title Sent To PubSubBroker {} Can't Publish.".format(title))
        return 0
