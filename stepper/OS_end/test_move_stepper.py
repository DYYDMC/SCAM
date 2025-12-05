from steppers import StepperController
stepper = StepperController()
stepper.initialize_connection()

# simple test
resp1 = stepper.move_to(2,3)
print("move_to response:", resp1)
resp2 = stepper.read_pos()
print("move_to response:", resp2)
resp3 = stepper.home_motor()
print("move_to response:", resp3)