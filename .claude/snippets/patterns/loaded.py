# From: services/video_service.py:49

    @property
    def loaded(self) -> bool:
        return self.cap is not None and self.cap.isOpened()
