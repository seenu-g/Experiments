import React from 'react';

class Car extends React.Component {
  constructor(props) {
    super(props);
      this.state = {
        brand: props.brand,
        model: props.model,
        color: props.color,
        year: props.year
      };
  }
  changeColor = () => {
    if(this.state.color === "red")
       this.setState({color: "blue"});
    else if(this.state.color === "blue")
       this.setState({color: "red"});
  }
  render() {
    return (
      <div>
        <p>
           {this.state.brand} -> {this.state.color} {this.state.model} from  {this.state.year}.
        </p>

        <button
          type="button" onClick={this.changeColor}> Change color
        </button>
      </div>
    );
  }
}
export default Car;