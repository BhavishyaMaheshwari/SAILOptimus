// This function takes another function as an argument (the controller)
// It returns a new anonymous function that executes the controller and catches any errors.
export default (fn) => {
  return (req, res, next) => {
    fn(req, res, next).catch(next); // .catch(err => next(err))
  };
};