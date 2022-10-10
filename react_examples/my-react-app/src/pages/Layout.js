import { Outlet, Link } from "react-router-dom";

// The <Outlet> renders the current route selected.
// <Link> is used to set the URL and keep track of browsing history,Use <Link> instead of <a href="">.

const Layout = () => {
  return (
    <>
      <nav>
        <ul>
          <li>
            <Link to="/">Home</Link>
          </li>
          <li>
            <Link to="/blogs">Blogs</Link>
          </li>
          <li>
            <Link to="/contact">Contact</Link>
          </li>
        </ul>
      </nav>

      <Outlet />
    </>
  )
};

export default Layout;