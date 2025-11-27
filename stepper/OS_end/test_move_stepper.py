from steppers import StepperController
stepper = StepperController()
stepper.initialize_connection()

# simple test
resp = stepper.move_rev(1)
print("Test response:", resp)
